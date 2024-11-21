"""Streaming tools related to the HDF5 format"""
from typing import Union, Dict, Optional, List
from contextlib import AbstractContextManager
from dataclasses import field, dataclass
from pathlib import Path
import logging

import numpy as np
import pandas as pd
from tables import File, Table, Filters

from battdat.io.hdf import write_df_to_table
from battdat.schemas.column import ColumnSchema, RawData
from battdat.schemas import BatteryMetadata
from battdat import __version__

logger = logging.getLogger(__name__)


@dataclass
class HDF5Writer(AbstractContextManager):
    """Tool to write raw time series data to an HDF5 file incrementally

    Writes data to the ``raw_data`` key of a different dataset."""

    # Attributes defining where and how to write
    hdf5_output: Union[Path, str, File]
    """File or already-open HDF5 file in which to store data"""
    metadata: BatteryMetadata = field(default_factory=BatteryMetadata)
    """Metadata describing the cell"""
    schema: ColumnSchema = field(default_factory=RawData)
    """Schema describing columns of the cell"""
    complevel: int = 0
    """Compression level. Can be between 0 (no compression) and 9 (maximum compression). Ignored if data table already exists"""
    complib: str = 'zlib'
    """Compression algorithm. Consult :func:`~pandas.read_hdf` for available options. Ignored if data table already exists"""
    key: str = ''
    """Name of the root group in which to store the data. Ignored if :attr:`hdf5_output` is a ``File``."""
    buffer_size: int = 32768
    """Number of rows to collect in memory before writing to disk"""

    # State used only while in writing mode
    _file: Optional[File] = None
    """Handle to an open file"""
    _dtype: Optional[np.dtype] = None
    """Dtype of records to be written"""
    _table: Optional[Table] = None
    """Pointer to the table being written"""
    _write_buffer: Optional[List[Dict]] = None
    """Index of the next step to be written"""

    def __enter__(self):
        self._write_buffer = list()

        # Open the store, if needed
        if isinstance(self.hdf5_output, File):
            self._file = self.hdf5_output
        else:
            self._file = File(
                self.hdf5_output,
                root_uep='/' + self.key,
                mode='w'
            )

        # Write metadata to the store's root's attributes
        root = self._file.root
        root._v_attrs.metadata = self.metadata.model_dump_json(exclude_none=True)
        root._v_attrs.json_schema = self.metadata.model_json_schema()
        root._v_attrs.battdat_version = __version__

        # Get the table if it exists already
        if 'raw_data' in root:
            self._table = root['raw_data']
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if len(self._write_buffer) > 0:  # Ensure last rows are written
            self.flush()
        if not isinstance(self.hdf5_output, File):  # Close file if a path was provided
            self._file.close()
        self._table = self._file = self._write_buffer = None

    def write_row(self, row: Dict[str, Union[str, float, int]]) -> int:
        """Add a row to the data file

        Args:
            row: Row to be added to the HDF5 file
        Returns:
            Number of rows written to file. Writes only occur when a write buffer has filled
        """
        self._write_buffer.append(row.copy())
        if len(self._write_buffer) >= self.buffer_size:
            return self.flush()
        return 0

    def flush(self) -> int:
        """Write the current row buffer to the file

        Returns:
            Number of rows written
        """

        if self._table is None:
            # Make the table the first time
            filters = Filters(complevel=self.complevel, complib=self.complib)
            df = pd.DataFrame(self._write_buffer)
            self._table = write_df_to_table(self._file, self._file.root, name='raw_data', filters=filters, df=df)

            # Store the metadata
            self._table.attrs.metadata = self.schema.model_dump_json()
            self._table.attrs.json_schema = self.schema.model_json_schema()
        else:
            # Append rows to the "raw_data" key
            row = np.empty((1,), dtype=self._table.dtype)
            known_names = set(self._table.dtype.names)
            for new_row in self._write_buffer:
                if (new_keys := set(new_row.keys())) != known_names:
                    logger.warning(f'Row has different keys than the Table. New keys: ({", ".join(new_keys.difference(known_names))}.'
                                   f' Missing: {", ".join(known_names.difference(new_keys))}')
                for c in known_names:
                    row[c] = new_row[c]
                self._table.append(row)

        written = len(self._write_buffer)
        self._write_buffer.clear()
        return written
