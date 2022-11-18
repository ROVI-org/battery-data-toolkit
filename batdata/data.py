"""Objects that represent battery datasets"""
from typing import Union, Optional

from pandas import HDFStore
from pandas.io.common import stringify_path
from pydantic import BaseModel
import pandas as pd
import h5py

from batdata.schemas import BatteryMetadata, CyclingData


class BatteryDataset:
    """Holder for all data associated with tests for a battery.

    Attributes of this class define different view of the data (e.g., raw time-series, per-cycle statistics)
    or different types of data (e.g., EIS) along with the metadata for the class

    I/O with BatteryDataFrame
    -------------------------

    This data frame provides I/O operations that store and retrieve the battery metadata into particular
    formats. The operations are named ``[to|from]_batdata_[format]``, where format could be one of

    - ``hdf``: Data is stored the `"table" format from PyTables
     <https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#hdf5-pytables>`_.
     Metadata are stored as an attribute to the
    - ``dict``: Data as a Python dictionary object with two keys: "metadata" for the battery metadata
        and "data" with the cycling data in "list" format ({"column"->["values"]})

    Many of methods use existing Pandas implementations of I/O operations, but with slight modifications
    to encode the metadata and to ensure a standardized format.

    """

    raw_data: Optional[pd.DataFrame]
    """Time-series data capturing the state of the battery as a function of time"""

    metadata: BatteryMetadata
    """Metadata fro the battery construction and testing"""

    def __init__(self, metadata: Union[BatteryMetadata, dict] = None, raw_data: Optional[pd.DataFrame] = None):
        """

        Parameters
        ----------
        metadata: BatteryMetadata or dict
            Metadata that describe the battery construction, data provenance and testing routines
        raw_data: pd.DataFrame
            Time-series data of the battery state
        """
        if metadata is None:
            metadata = {}
        elif isinstance(metadata, BaseModel):
            metadata = metadata.dict()
        self.metadata = BatteryMetadata(**metadata)
        self.raw_data = raw_data

    def validate_columns(self, allow_extra_columns: bool = True):
        """Determine whether the column types are appropriate

        Parameters
        ----------
        allow_extra_columns: bool
            Whether to allow unexpected columns

        Raises
        ------
        ValueError
            If the dataset fails validation
        """
        CyclingData.validate_dataframe(self.raw_data, allow_extra_columns)

    def to_batdata_hdf(self, path_or_buf, complevel=0, complib='zlib'):
        """Save the data in the standardized HDF5 file format

        This function wraps the ``to_hdf`` function of Pandas and supplies fixed values for some of the options
        so that the data is written in a reproducible format.

        Parameters
        ----------
        path_or_buf : str or pandas.HDFStore
            File path or HDFStore object.
        complevel : {0-9}, optional
            Specifies a compression level for data.
            A value of 0 disables compression.
        complib : {'zlib', 'lzo', 'bzip2', 'blosc'}, default 'zlib'
            Specifies the compression library to be used.
            As of v0.20.2 these additional compressors for Blosc are supported
            (default if no compressor specified: 'blosc:blosclz'):
            {'blosc:blosclz', 'blosc:lz4', 'blosc:lz4hc', 'blosc:snappy',
            'blosc:zlib', 'blosc:zstd'}.
            Specifying a compression library which is not available issues
            a ValueError.
        """

        # Store the various datasets
        #  Note that we use the "table" format to allow for partial reads / querying
        self.raw_data.to_hdf(path_or_buf, 'raw_data', complevel=complevel, complib=complib,
                             append=False, format='table', index=False)

        # Create logic for adding metadata
        def add_metadata(f: HDFStore):
            """Put the metadata in a standard location at the root of the HDF file"""
            f.root._v_attrs.metadata = self.metadata.json()

        # Apply the metadata addition function
        path_or_buf = stringify_path(path_or_buf)
        if isinstance(path_or_buf, str):
            with HDFStore(
                    path_or_buf, mode='a', complevel=complevel, complib=complib
            ) as store:
                add_metadata(store)
                store.flush()
        else:
            add_metadata(path_or_buf)

    @classmethod
    def from_batdata_hdf(cls, path_or_buf: Union[str, HDFStore]):
        """Read the battery data from an HDF file

        Parameters
        ----------
        path_or_buf : str or pandas.HDFStore
            File path or HDFStore object.
        """
        # Read the available datasets
        data = pd.read_hdf(path_or_buf, "raw_data")

        # Read out the battery metadata
        if isinstance(path_or_buf, str):
            with h5py.File(path_or_buf, 'r') as f:
                metadata = BatteryMetadata.parse_raw(f.attrs['metadata'])
        else:
            metadata = BatteryMetadata.parse_raw(path_or_buf.root._v_attrs.metadata)

        return cls(raw_data=data, metadata=metadata)

    def to_batdata_dict(self) -> dict:
        """Generate data in dictionary format

        Returns
        -------
            (dict) Data in dictionary format
        """
        return {
            'metadata': self.metadata.dict(),
            'raw_data': self.raw_data.to_dict('list')
        }

    @classmethod
    def from_batdata_dict(cls, d):
        """Read battery data and metadata from """
        return cls(raw_data=pd.DataFrame(d['raw_data']), metadata=d['metadata'])

    @staticmethod
    def get_metadata_from_hdf5(path: str) -> BatteryMetadata:
        """Open an HDF5 file and read only the metadata

        Parameters
        ----------
        path: str
            Path to an HDF5 file

        Returns
        -------
        metadata: BatteryMetadata
            Metadata from this file
        """

        with h5py.File(path, 'r') as f:
            return BatteryMetadata.parse_raw(f.attrs['metadata'])
