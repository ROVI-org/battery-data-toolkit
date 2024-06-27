"""Tools for streamlining upload to `Battery Archive <https://batteryarchive.org/>`_"""
from typing import Callable, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

import numpy as np
import pandas as pd

from .base import DatasetExporter
from ..data import BatteryDataset

logger = logging.getLogger(__name__)

# Mappings between our column names and theirs, with an optional function to perform conversion
# TODO (wardlt): Standardize fields for the cumulative charge and discharge for each cycle separately (#75)
# TODO (wardlt): Differentiate the cell temperature from the environment temperature (#76)
# TODO (wardlt): Compute more derived fields from BatteryArchive (#77)
_timeseries_reference: dict[str, tuple[str, Optional[Callable[[Any], Any]]]] = {
    'current': ('i', None),
    'voltage': ('v', None),
    'temperature': ('env_temperature', None),  # TODO (wardlt): @ypreger, would you prefer unknown temps as env or cell?
    'time': ('date_time', None),  # TODO (wardlt): This writes a UNIX timestep in UTC. Is that the form used by BA?
    'cycle_number': ('cycle_index', None),  # TODO (wardlt): Does BatteryArchive start at 0 or 1?
    'test_time': ('test_time', None),  # TODO (wardlt): What time units does BA use?
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

    def write_timeseries(self, data: pd.DataFrame, path: Path):
        """Write the time series dataset

        Args:
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

            # Save to disk
            chunk_path = path / f'cycle-timeseries-{i}.csv'
            out_chunk.to_csv(chunk_path, index=False, encoding='utf-8')
            logger.debug(f'Wrote {len(out_chunk)} rows to {chunk_path}')

    def export(self, dataset: BatteryDataset, path: Path):
        if dataset.raw_data is not None:
            self.write_timeseries(dataset.raw_data, path)
