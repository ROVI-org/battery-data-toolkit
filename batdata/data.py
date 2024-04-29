"""Objects that represent battery datasets"""
import shutil
import logging
import warnings
from pathlib import Path
from datetime import datetime
from typing import Union, Optional, Collection, List, Dict, Type, Set, Iterator, Tuple

from pandas import HDFStore
from pandas.io.common import stringify_path
from pydantic import BaseModel
from pyarrow import parquet as pq
from pyarrow import Table
import pandas as pd
import h5py

from batdata.schemas import BatteryMetadata
from batdata.schemas.cycling import RawData, CycleLevelData, ColumnSchema
from batdata.schemas.eis import EISData

_subsets: Dict[str, Type[ColumnSchema]] = {
    'raw_data': RawData,
    'cycle_stats': CycleLevelData,
    'eis_data': EISData
}
"""Mapping between subset and schema"""

logger = logging.getLogger(__name__)


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
    - ``parquet``: Data into a directory of `Parquet <https://parquet.apache.org/>`
        files for each types of data. The metadata for the dataset will be saved as well

    Many of methods use existing Pandas implementations of I/O operations, but with slight modifications
    to encode the metadata and to ensure a standardized format.

    """

    raw_data: Optional[pd.DataFrame] = None
    """Time-series data capturing the state of the battery as a function of time"""

    cycle_stats: Optional[pd.DataFrame] = None
    """Summary statistics of each cycle"""

    eis_data: Optional[pd.DataFrame] = None
    """Electrochemical Impedance Spectroscopy (EIS) data"""

    metadata: BatteryMetadata
    """Metadata for the battery construction and testing"""

    def __init__(self, metadata: Union[BatteryMetadata, dict] = None,
                 raw_data: Optional[pd.DataFrame] = None,
                 cycle_stats: Optional[pd.DataFrame] = None,
                 eis_data: Optional[pd.DataFrame] = None):
        """

        Parameters
        ----------
        metadata: BatteryMetadata or dict
            Metadata that describe the battery construction, data provenance and testing routines
        raw_data: pd.DataFrame
            Time-series data of the battery state
        cycle_stats: pd.DataFrame
            Summaries of each cycle
        eis_data: pd.DataFrame
            EIS data taken at multiple times
        """
        if metadata is None:
            metadata = {}
        elif isinstance(metadata, BaseModel):
            metadata = metadata.dict()
        self.metadata = BatteryMetadata(**metadata)
        self.raw_data = raw_data
        self.cycle_stats = cycle_stats
        self.eis_data = eis_data

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
        for attr_name, schema in _subsets.items():
            data = getattr(self, attr_name)
            if data is not None:
                schema.validate_dataframe(data, allow_extra_columns)

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

        # Check whether there are undocumented columns
        def _find_undefined_columns(data: pd.DataFrame, column_schema: Type[ColumnSchema]) -> List[str]:
            """Get the list of columns which are not defined in the schema"""

            cols = set(data.columns).difference(column_schema.model_fields)
            return list(cols)

        for attr_name, schema in _subsets.items():
            data = getattr(self, attr_name)
            defined_columns = getattr(self.metadata, f'{attr_name}_columns')
            if data is not None:
                new_cols = _find_undefined_columns(data, schema)
                undefined = set(new_cols).difference(defined_columns.keys())
                output.extend([f'Undefined column, {u}, in {attr_name}. Add a description into metadata.{attr_name}_columns'
                               for u in undefined])

        return output

    def to_batdata_hdf(self,
                       path_or_buf: Union[str, Path, HDFStore],
                       prefix: Optional[str] = None,
                       append: bool = False,
                       complevel: int = 0,
                       complib: str = 'zlib'):
        """Save the data in the standardized HDF5 file format

        This function wraps the ``to_hdf`` function of Pandas and supplies fixed values for some options
        so that the data is written in a reproducible format.

        Args:
            path_or_buf: File path or HDFStore object.
            prefix: Prefix to use to differentiate this battery from (optionally) others stored in this HDF5 file
            append: Whether to clear any existing data in the HDF5 file before writing
            complevel: Specifies a compression level for data. A value of 0 disables compression.
            complib: Specifies the compression library to be used.
        """

        # Delete the old file if present
        if isinstance(path_or_buf, (str, Path)) and (Path(path_or_buf).is_file() and not append):
            Path(path_or_buf).unlink()

        # Store the various datasets
        #  Note that we use the "table" format to allow for partial reads / querying
        for key in _subsets:
            data = getattr(self, key)
            if data is not None:
                if prefix is not None:
                    key = f'{prefix}-{key}'
                data.to_hdf(path_or_buf, key, complevel=complevel,
                            complib=complib, append=False, format='table',
                            index=False)

        # Create logic for adding metadata
        def add_metadata(f: HDFStore):
            """Put the metadata in a standard location at the root of the HDF file"""
            f.root._v_attrs.metadata = self.metadata.json()

        # Apply the metadata addition function
        path_or_buf = stringify_path(path_or_buf)
        if isinstance(path_or_buf, (str, Path)):
            with HDFStore(
                    path_or_buf, mode='a', complevel=complevel, complib=complib
            ) as store:
                add_metadata(store)
                store.flush()
        else:
            add_metadata(path_or_buf)

    @classmethod
    def from_batdata_hdf(cls,
                         path_or_buf: Union[str, Path, HDFStore],
                         subsets: Optional[Collection[str]] = None,
                         prefix: Optional[str] = None):
        """Read the battery data from an HDF file

        Args:
            path_or_buf: File path or HDFStore object
            subsets : Which subsets of data to read from the data file (e.g., raw_data, cycle_stats)
            prefix: Prefix designating which battery extract from this file, if there are multiple datasets
        """

        # Determine which datasets to read
        read_all = False
        if subsets is None:
            subsets = _subsets
            read_all = True

        data = {}
        for subset in subsets:
            # Throw error if user provides an unknown subset name
            if subset not in _subsets:
                raise ValueError(f'Unknown subset: {subset}')

            # Prepend the prefix
            if prefix is not None:
                key = f'{prefix}-{subset}'
            else:
                key = subset

            try:
                data[subset] = pd.read_hdf(path_or_buf, key)
            except KeyError as exc:
                if read_all:
                    continue
                else:
                    raise ValueError(f'File does not contain {key}') from exc

        # Read out the battery metadata
        if isinstance(path_or_buf, (str, Path)):
            with h5py.File(path_or_buf, 'r') as f:
                metadata = BatteryMetadata.model_validate_json(f.attrs['metadata'])
        else:
            metadata = BatteryMetadata.model_validate_json(path_or_buf.root._v_attrs.metadata)

        return cls(**data, metadata=metadata)

    @classmethod
    def all_cells_from_batdata_hdf(cls, path: Union[str, Path], subsets: Optional[Collection[str]] = None) -> Iterator[Tuple[str, 'BatteryDataset']]:
        """Iterate over all cells in an HDF file

        Args:
            path: Path to the HDF file
            subsets : Which subsets of data to read from the data file (e.g., raw_data, cycle_stats)
        Yields:
            - Name of the cell
            - Cell data
        """

        # Start by gathering all names of the cells
        _, names = cls.inspect_batdata_hdf(path)

        with HDFStore(path, mode='r') as fp:  # Only open once
            for name in names:
                yield name, cls.from_batdata_hdf(fp, prefix=name, subsets=subsets)

    @staticmethod
    def inspect_batdata_hdf(path: Union[str, Path]) -> tuple[BatteryMetadata, Set[Optional[str]]]:
        """Extract the battery data and the names of cells contained within an HDF5 file

        Args:
            path: Path to the HDF5 file
        Returns:
            - Metadata from this file
            - List of names of batteries stored within the file
        """

        with h5py.File(path, 'r') as f:
            metadata = BatteryMetadata.model_validate_json(f.attrs['metadata'])

            # Get the names by gathering all names before the "-" in group names
            names = set()
            for key in f.keys():
                if '-' not in key:  # From the "default" group
                    names.add(None)
                name, _ = key.rsplit("-", 1)
                names.add(name)
            return metadata, names

    @staticmethod
    def get_metadata_from_hdf5(path: Union[str, Path]) -> BatteryMetadata:
        """Get battery metadata from an HDF file without reading the data

        Args:
            path: Path to the HDF5 file

        Returns:
            Metadata from this file
        """

        with h5py.File(path, 'r') as f:
            return BatteryMetadata.model_validate_json(f.attrs['metadata'])

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

        # Convert the keys to a dataframe
        inputs = d.copy()
        for k in _subsets:
            if k in inputs:
                inputs[k] = pd.DataFrame(d[k])
        return cls(**inputs)

    def to_batdata_parquet(self, path: Union[Path, str], overwrite: bool = True) -> Dict[str, Path]:
        """Write battery data to a directory of Parquet files

        Args:
            path: Path in which to write to
            overwrite: Whether to overwrite an existing directory
        Returns:
            Map of the name of the subset to
        """
        # Handle existing paths
        path = Path(path)
        if path.exists():
            if not overwrite:
                raise ValueError(f'Path already exists and overwrite is disabled: {path}')
            logger.info(f'Deleting existing directory at {path}')
            shutil.rmtree(path)

        # Make the output directory, then write each Parquet file
        path.mkdir(parents=True, exist_ok=False)
        my_metadata = {
            'battery_metadata': self.metadata.json(exclude_defaults=True),
            'write_date': datetime.now().isoformat()
        }
        written = {}
        for key in _subsets:
            if (data := getattr(self, key)) is None:
                continue
            # Put the metadata for the battery into the table's schema
            #  TODO (wardlt): Figure out if it can go in the file-metadata
            data_path = path / f'{key}.parquet'
            table = Table.from_pandas(data, preserve_index=False)
            new_schema = table.schema.with_metadata({**my_metadata, **table.schema.metadata})
            table = table.cast(new_schema)
            pq.write_table(table, where=data_path)

            written[key] = data_path
        return written

    @classmethod
    def from_batdata_parquet(cls, path: Union[str, Path], subsets: Optional[Collection[str]] = None):
        """Read the battery data from an HDF file

        Args:
            path: Path to a directory containing parquet files for a specific batter
            subsets: Which subsets of data to read from the data file (e.g., raw_data, cycle_stats)
        """

        # Find the parquet files, if no specification is listed
        path = Path(path)
        if subsets is None:
            subsets = [p.with_suffix('').name for p in path.glob('*.parquet')]

        if len(subsets) == 0:
            raise ValueError(f'No data available for {path}')

        # Load each subset
        metadata = None
        data = {}
        for subset in subsets:
            data_path = path / f'{subset}.parquet'
            table = pq.read_table(data_path)
            data[subset] = table

            # Load or check the metadata
            if b'battery_metadata' not in table.schema.metadata:
                warnings.warn(f'Metadata not found in {data_path}')
                continue

            my_metadata = table.schema.metadata[b'battery_metadata']
            if metadata is None:
                metadata = my_metadata
            elif my_metadata != metadata:
                warnings.warn(f'Battery data different for files in {path}')

        return cls(
            metadata=BatteryMetadata.model_validate_json(metadata),
            **data
        )

    @staticmethod
    def get_metadata_from_parquet(path: Union[str, Path]) -> BatteryMetadata:
        """Get battery metadata from a directory of parquet files without reading them

        Args:
            path: Path to the directory of Parquet files

        Returns:
            Metadata from the files
        """

        # Get a parquet file
        path = Path(path)
        if path.is_file():
            pq_path = path
        else:
            pq_path = next(path.glob('*.parquet'), None)
            if pq_path is None:
                raise ValueError(f'No parquet files in {path}')

        # Read the metadata from the schema
        schema = pq.read_schema(pq_path)
        if b'battery_metadata' not in schema.metadata:
            raise ValueError(f'No metadata in {pq_path}')
        return BatteryMetadata.model_validate_json(schema.metadata[b'battery_metadata'])
