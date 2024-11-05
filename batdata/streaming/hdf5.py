"""Streaming tools related to the HDF5 format"""
from typing import Union, Dict, Optional, List
from contextlib import AbstractContextManager
from dataclasses import field, dataclass
from pathlib import Path

import pandas as pd

from batdata.schemas import BatteryMetadata


@dataclass
class HDF5Writer(AbstractContextManager):
    """Tool to write raw time series data to an HDF5 file incrementally

    Args:
        hdf5_output: Path to a location on disk or the root group in an HDF5 file in which to write data.
        storage_key: Name of the group within the file to store all states
    """

    # Attributes defining where and how to write
    hdf5_output: Union[Path, str, pd.HDFStore]
    """File or already-open HDF5 file in which to store data"""
    metadata: BatteryMetadata = field(default_factory=BatteryMetadata)
    """Metadata describing the cell"""
    complevel: Optional[int] = None
    """Compression level. Can be between 0 (no compression) and 9 (maximum compression). Ignored if :attr:`hdf5_output` is a ``HDFStore``."""
    complib: str = 'zlib'
    """Compression algorithm. Consult :func:`~pandas.read_hdf` for available options. Ignored if :attr:`hdf5_output` is a ``HDFStore``."""
    key: str = ''
    """Name of the root group in which to store the data. Ignored if :attr:`hdf5_output` is a ``HDFStore``."""
    buffer_size: int = 32768
    """Number of rows to collect in memory before writing to disk"""

    # State used only while in writing mode
    _store: Optional[pd.HDFStore] = None
    """Handle to an open file"""
    _write_buffer: Optional[List[Dict]] = None
    """Index of the next step to be written"""

    def __enter__(self):
        self._write_buffer = list()

        # Open the store, if needed
        if isinstance(self.hdf5_output, pd.HDFStore):
            self._store = self.hdf5_output
        else:
            self._store = pd.HDFStore(
                self.hdf5_output,
                complevel=self.complevel,
                complib=self.complib,
                root_uep=f'{self.key}',
            )

        # Write metadata to the store's root's attributes
        self._store.root._v_attrs.metadata = self.metadata.model_dump_json(exclude_none=True)
        self._store.root._v_attrs.schema = self.metadata.model_json_schema()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if len(self._write_buffer) > 0:  # Ensure last rows are written
            self.flush()
        if not isinstance(self.hdf5_output, pd.HDFStore):  # Close file if a path was provided
            self._store.close()
        self._write_buffer = None

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

        # Append rows to the "raw_data" key
        to_write = pd.DataFrame(self._write_buffer)
        self._write_buffer.clear()
        self._store.append('raw_data', to_write)
        return len(to_write)
