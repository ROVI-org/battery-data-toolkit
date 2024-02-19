"""Parse from the CSV formats of batterydata.energy.gov"""
import re
import logging
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Union, List, Iterator, Tuple, Optional

import pandas as pd

from .base import BatteryDataExtractor
from ..data import BatteryDataset
from ..schemas import BatteryMetadata

_fname_match = re.compile(r'(?P<name>[-\w]+)-(?P<type>summary|raw)\.csv')

logger = logging.getLogger(__name__)

# TODO (wardlt): Columns that yet to have a home in the schema:
#  - Cell2
_name_map_raw = {
    'Cycle_Index': 'cycle_index',
    'Step': 'step_index',
    'Time_s': 'test_time',
    'Current_A': 'current',
    'Voltage_V': 'voltage',
    'Cell_Temperature_C': 'temperature',
    'Datenum_d': 'time'
}


def convert_raw_signal_to_batdata(input_df: pd.DataFrame, store_all: bool) -> pd.DataFrame:
    """Convert a cycle statistics dataframe to one using batdata names and conventions

    Args:
        input_df: Initial NREL-format dataframe
        store_all: Whether to store columns even we have not defined their names
    Returns:
        DataFrame in the batdata format
    """
    output = pd.DataFrame()

    # Rename columns that are otherwise the same
    for orig, new in _name_map_raw.items():
        output[new] = input_df[orig]

    # Decrement the indices from 1-indexed to 0-indexed
    output[['cycle_index', 'step_index']] -= 1

    # Convert the date to POSIX timestamp (ease of use in Python) from days from 1/1/0000
    begin_time = datetime(year=1, month=1, day=1)
    output['time'] = output['time'].apply(lambda x: (timedelta(days=x - 366) + begin_time).timestamp())

    # Reverse the sign of current
    output['current'] *= -1

    # Add all other columns as-is
    if store_all:
        for col in input_df.columns:
            if col not in _name_map_raw:
                output[col] = input_df[col]

    return output


_name_map_summary = {
    'Cycle_Index': 'cycle_number',
    'Q_chg': 'charge_capacity',
    'E_chg': 'charge_energy',
    'Q_dis': 'discharge_capacity',
    'E_dis': 'discharge_energy',
    'CE': 'coulomb_efficiency',
    'EE': 'energy_efficiency',
    'tsecs_start': 'cycle_start',
    'tsecs_cycle': 'cycle_duration',
    'T_min': 'temperature_minimum',
    'T_max': 'temperature_maximum',
    'T_avg': 'temperature_average',
}


def convert_summary_to_batdata(input_df: pd.DataFrame, store_all: bool) -> pd.DataFrame:
    """Convert the summary dataframe to a format using batdata names and conventions

    Args:
        input_df: Initial NREL-format dataframe
        store_all: Whether to store columns even we have not defined their names
    Returns:
        DataFrame in the batdata format
    """

    output = pd.DataFrame()

    # Rename columns that are otherwise the same
    for orig, new in _name_map_summary.items():
        output[new] = input_df[orig]

    # Convert charge and discharge energy from W-hr to J
    for c in ['charge_energy', 'discharge_energy']:
        output[c] /= 3600

    # Add all other columns as-is
    if store_all:
        for col in input_df.columns:
            if col not in _name_map_summary:
                output[col] = input_df[col]

    return output


@dataclass
class BDExtractor(BatteryDataExtractor):
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

    def parse_to_dataframe(self, group: List[str],
                           metadata: Optional[Union[BatteryMetadata, dict]] = None) -> BatteryDataset:
        # Make an empty metadata if none available
        if metadata is None:
            metadata = BatteryMetadata()

        # Process each file
        raw_data = cycle_stats = None
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
                cycle_stats = convert_summary_to_batdata(pd.read_csv(path), self.store_all)
            elif data_type == 'raw':
                raw_data = convert_raw_signal_to_batdata(pd.read_csv(path), self.store_all)
            else:
                raise ValueError(f'Data type unrecognized: {data_type}')

        return BatteryDataset(raw_data=raw_data, cycle_stats=cycle_stats, metadata=metadata)

    def implementors(self) -> List[str]:
        return ['Logan Ward <lward@anl.gov>']

    def version(self) -> str:
        return '0.0.1'
