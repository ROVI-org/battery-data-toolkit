"""Objects that represent battery datasets"""
from typing import Union, Optional, Collection, List

from pandas import HDFStore
from pandas.io.common import stringify_path
from pydantic import BaseModel
import pandas as pd
import h5py

from batdata.schemas import BatteryMetadata
from batdata.schemas.cycling import RawData, CycleLevelData, ColumnSchema

_subsets = ('raw_data', 'cycle_stats')


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

    raw_data: Optional[pd.DataFrame] = None
    """Time-series data capturing the state of the battery as a function of time"""

    cycle_stats: Optional[pd.DataFrame] = None
    """Summary statistics of each cycle"""

    metadata: BatteryMetadata
    """Metadata for the battery construction and testing"""

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
        if self.raw_data is not None:
            RawData.validate_dataframe(self.raw_data, allow_extra_columns)
        if self.cycle_stats is not None:
            CycleLevelData.validate_dataframe(self.raw_data, allow_extra_columns)

    def validate(self) -> List[str]:
        """Validate the data stored in this object

        Ensures that the data are valid according to schemas and
        makes recommendations of improvements that one could make
        to increase the re-usability of the data.

        Returns
        -------
        List of str
            Recommendations to improve data re-use
        """
        self.validate_columns()
        output = []

        # Mapping between subset and schema
        _schemas = {
            'raw_data': RawData,
            'cycle_stats': CycleLevelData
        }

        # Check whether there are undocumented columns
        def _find_undefined_columns(data: pd.DataFrame, column_schema: ColumnSchema) -> List[str]:
            """Get the list of columns which are not defined in the schema"""

            cols = set(data.columns).difference(column_schema.__fields__)
            return list(cols)

        for subset in _subsets:
            data = getattr(self, subset)
            defined_columns = getattr(self.metadata, f'{subset}_columns')
            if data is not None:
                new_cols = _find_undefined_columns(data, _schemas[subset])
                undefined = set(new_cols).difference(defined_columns.keys())
                output.extend([f'Undefined column, {u}, in {subset}. Add a description into metadata.{subset}_columns'
                               for u in undefined])

        return output

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
        if self.raw_data is not None:
            self.raw_data.to_hdf(path_or_buf, 'raw_data', complevel=complevel, complib=complib,
                                 append=False, format='table', index=False)
        if self.cycle_stats is not None:
            self.cycle_stats.to_hdf(path_or_buf, 'cycle_stats', complevel=complevel, complib=complib,
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
    def from_batdata_hdf(cls, path_or_buf: Union[str, HDFStore], subsets: Optional[Collection[str]] = None):
        """Read the battery data from an HDF file

        Parameters
        ----------
        path_or_buf : str or pandas.HDFStore
            File path or HDFStore object.
        subsets : List of strings
            Which subsets of data to read from the data file (e.g., raw_data, cycle_stats)
        """

        # Determine which datasets to read
        read_all = False
        if subsets is None:
            subsets = _subsets
            read_all = True

        data = {}
        for key in subsets:
            if key not in _subsets:
                raise ValueError(f'Unknown subset: {key}')

            try:
                data[key] = pd.read_hdf(path_or_buf, key)
            except KeyError as exc:
                if read_all:
                    continue
                else:
                    raise ValueError(f'File does not contain {key}') from exc

        # Read out the battery metadata
        if isinstance(path_or_buf, str):
            with h5py.File(path_or_buf, 'r') as f:
                metadata = BatteryMetadata.parse_raw(f.attrs['metadata'])
        else:
            metadata = BatteryMetadata.parse_raw(path_or_buf.root._v_attrs.metadata)

        return cls(**data, metadata=metadata)

    def to_batdata_dict(self) -> dict:
        """Generate data in dictionary format

        Returns
        -------
            (dict) Data in dictionary format
        """

        output = {'metadata': self.metadata.dict()}
        for key in _subsets:
            data = getattr(self, key)
            if data is not None:
                output[key] = data.to_dict('list')

        return output

    @classmethod
    def from_batdata_dict(cls, d):
        """Read battery data and metadata from a dictionary format"""

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
