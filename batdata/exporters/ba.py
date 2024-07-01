"""Tools for streamlining upload to `Battery Archive <https://batteryarchive.org/>`_"""

from typing import Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import logging
import json

import numpy as np
import pandas as pd

from .base import DatasetExporter
from ..data import BatteryDataset
from ..schemas import BatteryMetadata

logger = logging.getLogger(__name__)

# Mappings between our column names and theirs, with an optional function to perform conversion
# TODO (wardlt): Standardize fields for the cumulative charge and discharge for each cycle separately (#75)
# TODO (wardlt): Differentiate the cell temperature from the environment temperature (#76)
# TODO (wardlt): Compute more derived fields from BatteryArchive (#77)
_timeseries_reference: dict[str, tuple[str, Optional[Callable[[Any], Any]]]] = {
    'current': ('i', None),
    'voltage': ('v', None),
    'temperature': ('env_temperature', None),  # TODO (wardlt): @ypreger, would you prefer unknown temps as env or cell?
    'time': ('date_time', lambda x: datetime.fromtimestamp(x).strftime('%m/%d/%Y %H:%M:%S.%f')),
    'cycle_number': ('cycle_index', lambda x: x + 1),  # BA starts indices from 1
    'test_time': ('test_time', None),
}

_battery_metadata_reference: dict[str, str] = {
    'nominal_capacity': 'ah',  # TODO (wardlt): Why is ah an integer?
    'form_factor': 'form_factor',
    'mass': 'weight',  # TODO (wardlt): What units does batteryachive use?
    'dimensions': 'dimensions',  # TODO (wardlt): How do you express shapes for different form factors
}

_metadata_reference: dict[str, str] = {
    'source': 'source',
}


# TODO (wardlt): Reconsider saving in CSV. Parquet would preserve data types

@dataclass
class BatteryArchiveExporter(DatasetExporter):
    """Export data into CSV files that follow the format definitions used in BatteryArchive

    The exporter writes files for each table in the
    `Battery Archive SQL schema <https://github.com/battery-lcf/batteryarchive-agent/blob/main/data/ba_data_schema.sql>`_
    with column names matches to their definitions.
    """

    chunk_size: int = 100000
    """Maximum number of rows to write to disk in a single CSV file"""

    def write_timeseries(self, cell_id: str, data: pd.DataFrame, path: Path):
        """Write the time series dataset

        Args:
            cell_id: Name for the cell, used as a foreign key to map between tables
            data: Time series data to write to disk
            path: Root path for writing cycling data
        """

        num_chunks = len(data) // self.chunk_size + 1
        logger.info(f'Writing time series data to disk in {num_chunks} chunks')
        for i, chunk in enumerate(np.array_split(data, num_chunks)):
            # Convert all of our columns
            out_chunk = pd.DataFrame()
            for my_col, (out_col, out_fun) in _timeseries_reference.items():
                if my_col in chunk:
                    out_chunk[out_col] = chunk[my_col]
                    if out_fun is not None:
                        out_chunk[out_col] = out_chunk[out_col].apply(out_fun)

            # Add a cell id to the frame
            out_chunk['cell_id'] = cell_id

            # Save to disk
            chunk_path = path / f'cycle-timeseries-{i}.csv'
            out_chunk.to_csv(chunk_path, index=False, encoding='utf-8')
            logger.debug(f'Wrote {len(out_chunk)} rows to {chunk_path}')

    def write_metadata(self, cell_id: str, metadata: BatteryMetadata, path: Path):
        """Write the metadata into a JSON file

        Args:
            cell_id: ID for the cell
            metadata: Metadata to be written
            path: Path in which to write the data
        """

        output = {'cell_id': cell_id}

        # Write the materials for the anode and cathode as dictionaries
        for terminal in ['anode', 'cathode']:
            attr = getattr(metadata.battery, terminal, None)
            if attr is not None:
                output[terminal] = attr.model_dump_json(exclude_unset=True)

        # Write the simple fields about the batteries and tester
        for my_field, ba_field in _battery_metadata_reference.items():
            attr = getattr(metadata.battery, my_field, None)
            if attr is not None:
                output[ba_field] = attr

        for my_field, ba_field in _metadata_reference.items():
            attr = getattr(metadata, my_field, None)
            if attr is not None:
                output[ba_field] = attr

        with open(path / 'metadata.json', 'w') as fp:
            json.dump(output, fp)

    def export(self, dataset: BatteryDataset, path: Path):
        cell_name = dataset.metadata.name or str(uuid4())  # Default to UUID if none provided

        if dataset.raw_data is not None:
            self.write_timeseries(cell_name, dataset.raw_data, path)

        if dataset.metadata is not None:
            self.write_metadata(cell_name, dataset.metadata, path)
