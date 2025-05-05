"""Parse from the CSV formats of batterydata.energy.gov"""
import re
import logging
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Union, List, Iterator, Tuple, Optional, Iterable

import pandas as pd

from battdat.data import BatteryDataset
from battdat.io.base import DatasetFileReader
from battdat.schemas import BatteryMetadata, BatteryDescription

_fname_match = re.compile(r'(?P<name>[-\w]+)-(?P<type>summary|raw)\.csv')

logger = logging.getLogger(__name__)


def generate_metadata(desc: dict, associated_ids: Iterable[str] = ()) -> BatteryMetadata:
    """Assemble the battery metadata for a dataset

    The metadata for a single dataset are all the same and available by querying
    the ``https://batterydata.energy.gov/api/3/action/package_show?id={dataset_id}``
    endpoint of `Battery Data Hub <https://batterydata.energy.gov/>`_.

    Args:
        desc: Data from the CKAN metadata response
        associated_ids: List of other resources associated with this dataset, such as the DOIs of papers.
    Returns:
        Metadata for the cell provenance and construction
    """

    # Get the "results" pane if users didn't provide it
    if 'result' in desc:
        desc = desc['result']

    # Describe the battery
    battery = BatteryDescription(
        manufacturer=desc['manufacturer_supplier'],
        design=", ".join(desc['cell_type']),
        anode={'name': ", ".join(desc['negative_electrode'])},
        cathode={'name': ", ".join(desc['positive_electrode'])},
        electrolyte={'name': ", ".join(desc['electrolyte_class_dataset'])},
        nominal_capacity=desc['nominal_cell_capacity'],
    )

    # Describe the context of when it was tested
    return BatteryMetadata(
        source=desc['organization']['title'],
        dataset_name=desc['title'],
        associated_ids=associated_ids,
        battery=battery,
    )


# TODO (wardlt): Columns that yet to have a home in the schema:
#  - Cell2
_name_map_raw = {
    'Cycle_Index': 'cycle_number',
    'Step': 'step_index',
    'Time_s': 'test_time',
    'Current_A': 'current',
    'Voltage_V': 'voltage',
    'Cell_Temperature_C': 'temperature',
    'Datenum_d': 'time'
}


def convert_raw_signal(input_df: pd.DataFrame, store_all: bool) -> pd.DataFrame:
    """Convert a cycle statistics dataframe to one using battdat names and conventions

    Args:
        input_df: Initial NREL-format dataframe
        store_all: Whether to store columns even we have not defined their names
    Returns:
        DataFrame in the battdat format
    """
    output = pd.DataFrame()

    # Rename columns that are otherwise the same
    for orig, new in _name_map_raw.items():
        output[new] = input_df[orig]

    # Decrement the indices from 1-indexed to 0-indexed
    output[['cycle_number', 'step_index']] -= 1

    # Convert the date to POSIX timestamp (ease of use in Python) from days from 1/1/0000
    begin_time = datetime(year=1, month=1, day=1)
    output['time'] = output['time'].apply(lambda x: (timedelta(days=x - 366) + begin_time).timestamp())

    # Add all other columns as-is
    if store_all:
        for col in input_df.columns:
            if col not in _name_map_raw:
                output[col] = input_df[col]

    return output


_name_map_summary = {
    'Cycle_Index': 'cycle_number',
    'Q_chg': 'capacity_charge',
    'E_chg': 'energy_charge',
    'Q_dis': 'capacity_discharge',
    'E_dis': 'energy_discharge',
    'CE': 'coulomb_efficiency',
    'EE': 'energy_efficiency',
    'tsecs_start': 'cycle_start',
    'tsecs_cycle': 'cycle_duration',
    'T_min': 'temperature_minimum',
    'T_max': 'temperature_maximum',
    'T_avg': 'temperature_average',
}


def convert_summary(input_df: pd.DataFrame, store_all: bool) -> pd.DataFrame:
    """Convert the summary dataframe to a format using battdat names and conventions

    Args:
        input_df: Initial NREL-format dataframe
        store_all: Whether to store columns even we have not defined their names
    Returns:
        DataFrame in the battdat format
    """

    output = pd.DataFrame()

    # Rename columns that are otherwise the same
    for orig, new in _name_map_summary.items():
        output[new] = input_df[orig]

    # Add all other columns as-is
    if store_all:
        for col in input_df.columns:
            if col not in _name_map_summary:
                output[col] = input_df[col]

    return output


def convert_eis_data(input_df: pd.DataFrame) -> pd.DataFrame:
    """Rename the columns from an NREL-standard set of EIS data to our names and conventions

    Args:
        input_df: NREL-format raw data
    Returns:
        EIS data in battdat format
    """

    # Filter out the non-EIS data
    input_df = input_df[~input_df['Frequency_Hz'].isnull()]

    # Use the cycle index as a test index
    output = pd.DataFrame()
    output['test_id'] = input_df['Cycle_Index']

    # Drop units off and make lower case
    cols = ['Frequency_Hz', 'Z_Imag_Ohm', 'Z_Real_Ohm', 'Z_Mag_Ohm', 'Z_Phase_Degree']
    for col in cols:
        my_name = "_".join(col.lower().split("_")[:-1])
        output[my_name] = input_df[col]
    return output


@dataclass
class BDReader(DatasetFileReader):
    """Read data from the batterydata.energy.gov CSV format

    Every cell in batterydata.energy.gov is stored as two separate CSV files for each battery,
    "<cell_name>-summary.csv" for the cycle-level summaries
    and "<cell_name>-raw.csv" for the time series measurements.
    Metadata is held in an Excel file, "metadata.xlsx," in the same directory."""

    store_all: bool = False
    """Store all data from the original data, even if we have not defined it"""

    def group(self, files: Union[str, List[str]], directories: List[str] = None,
              context: dict = None) -> Iterator[Tuple[str, ...]]:

        # Find files that match the CSV naming convention
        groups = defaultdict(list)  # Map of cell name to the output
        for file in files:
            if (match := _fname_match.match(Path(file).name)) is not None:
                groups[match.group('name')].append(file)

        yield from groups.values()

    def read_dataset(self,
                     group: List[str],
                     metadata: Optional[Union[BatteryMetadata, dict]] = None) -> BatteryDataset:
        # Make an empty metadata if none available
        if metadata is None:
            metadata = BatteryMetadata()

        # Process each file
        raw_data = cycle_stats = eis_data = None
        for path in group:
            match = _fname_match.match(Path(path).name)
            if match is None:
                raise ValueError(f'Filename convention broken for {path}. Should be <cell_name>-<summary|raw>.csv')

            # Update the name in the metadata
            if metadata.name is None:
                metadata.name = match.group('name')

            # Different parsing logic by type
            data_type = match.group('type')
            if data_type == 'summary':
                cycle_stats = convert_summary(pd.read_csv(path), self.store_all)
            elif data_type == 'raw':
                nrel_data = pd.read_csv(path)
                raw_data = convert_raw_signal(nrel_data, self.store_all)

                # Get EIS data, if available
                if 'Z_Imag_Ohm' in nrel_data.columns and not (nrel_data['Z_Imag_Ohm'].isna()).all():
                    eis_data = convert_eis_data(nrel_data)
            else:
                raise ValueError(f'Data type unrecognized: {data_type}')

        # Separate out the EIS data, if possible
        return BatteryDataset.make_cell_dataset(raw_data=raw_data, cycle_stats=cycle_stats, eis_data=eis_data, metadata=metadata)
