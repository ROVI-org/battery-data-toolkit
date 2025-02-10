"""Objects that represent battery datasets"""
import logging
import warnings
from pathlib import Path
from typing import Union, Optional, Collection, List, Dict, Set, Iterator, Tuple, Mapping

from pydantic import BaseModel, ValidationError
from tables import File
import pandas as pd

from battdat.schemas import BatteryMetadata
from battdat.schemas.column import RawData, CycleLevelData, ColumnSchema
from battdat.schemas.eis import EISData
from battdat import __version__

logger = logging.getLogger(__name__)


class BatteryDataset(Mapping[str, pd.DataFrame]):
    """Base class for all battery datasets.

    Not to be created directly by users. Defines the functions to validate, read, and write from HDF5 or Parquet files.

    Args:
        tables: Subsets which compose this larger dataset
        metadata: Metadata for the entire dataset
        schemas: Schemas describing each subset
        check_schemas: Whether to throw an error if datasets lack a schema
    """

    metadata: BatteryMetadata
    """Information describing the source of a dataset"""
    schemas: Dict[str, ColumnSchema]
    """Schemas describing each dataset"""
    tables: Dict[str, pd.DataFrame]
    """Datasets available for users"""

    def __init__(self,
                 tables: Dict[str, pd.DataFrame],
                 schemas: Dict[str, ColumnSchema],
                 metadata: BatteryMetadata = None,
                 check_schemas: bool = True):
        self.schemas = schemas.copy()
        self.tables = tables.copy()

        # Assign default metadata
        if metadata is None:
            metadata = {}
        elif isinstance(metadata, BaseModel):
            metadata = metadata.model_dump()

        # Warn if the version of the metadata is different
        version_mismatch = False
        if (supplied_version := metadata.get('version', __version__)) != __version__:
            version_mismatch = True
            warnings.warn(f'Metadata was created in a different version of battdat. supplied={supplied_version}, current={__version__}.')
        try:
            self.metadata = BatteryMetadata(**metadata)
        except ValidationError:
            if version_mismatch:
                warnings.warn('Metadata failed to validate, probably due to version mismatch. Discarding until we support backwards compatibility')
                self.metadata = BatteryMetadata()
            else:
                raise

        # Check if schemas are missing for some datasets
        missing_schema = set(self.tables.keys()).difference(self.schemas)
        if len(missing_schema) > 0:
            warn_msg = f'Missing schema for some datasets: {", ".join(missing_schema)}'
            logger.warning(warn_msg)
            if check_schemas:
                raise ValueError(warn_msg)

    def __getitem__(self, item: str) -> pd.DataFrame:
        """Access a specific table within the dataset"""
        return self.tables[item]

    def __contains__(self, item):
        """Whether the dataset contains a specific table"""
        return item in self.tables

    def __len__(self):
        return len(self.tables)

    def __iter__(self):
        return iter(self.tables.items())

    def validate_columns(self, allow_extra_columns: bool = True):
        """Determine whether the column types are appropriate

        Args:
            allow_extra_columns: Whether to allow unexpected columns

        Raises
            (ValueError): If the dataset fails validation
        """
        for attr_name, schema in self.schemas.items():
            if (data := self.tables.get(attr_name)) is not None:
                schema.validate_dataframe(data, allow_extra_columns)

    def validate(self) -> List[str]:
        """Validate the data stored in this object

        Ensures that the data are valid according to schemas and
        makes recommendations of improvements that one could make
        to increase the re-usability of the data.

        Returns:
            Recommendations to improve data re-use
        """
        self.validate_columns()
        output = []

        for attr_name, schema in self.schemas.items():
            if (data := self.tables.get(attr_name)) is not None:
                undefined = set(data.columns).difference(schema.column_names)
                output.extend([f'Undefined column, {u}, in {attr_name}. Add a description into schemas.{attr_name}.extra_columns'
                               for u in undefined])

        return output

    def to_hdf(self,
               path_or_buf: Union[str, Path, File],
               prefix: Optional[str] = None,
               overwrite: bool = True,
               complevel: int = 0,
               complib: str = 'zlib'):
        """Save the data in the standardized HDF5 file format

        This function wraps the ``to_hdf`` function of Pandas and supplies fixed values for some options
        so that the data is written in a reproducible format.

        Args:
            path_or_buf: File path or HDFStore object.
            prefix: Prefix to use to differentiate this battery from (optionally) others stored in this HDF5 file
            overwrite: Whether to delete an existing HDF5 file
            complevel: Specifies a compression level for data. A value of 0 disables compression.
            complib: Specifies the compression library to be used.
        """
        # Delete existing file if present
        if overwrite and isinstance(path_or_buf, (str, Path)) and Path(path_or_buf).is_file():
            Path(path_or_buf).unlink()

        from battdat.io.hdf import HDF5Writer, as_hdf5_object
        writer = HDF5Writer(complib=complib, complevel=complevel)
        with as_hdf5_object(path_or_buf, mode='w' if overwrite else 'a') as file:
            writer.write_to_hdf(self, file=file, prefix=prefix)

    @classmethod
    def from_hdf(cls,
                 path_or_buf: Union[str, Path, File],
                 tables: Optional[Collection[str]] = None,
                 prefix: Union[str, int] = None) -> 'BatteryDataset':
        """Read the battery data from an HDF file

        Use :meth:`all_cells_from_hdf` to read all datasets from a file.

        Args:
            path_or_buf: File path or HDFStore object
            tables : Which subsets of data to read from the data file (e.g., raw_data, cycle_stats)
            prefix: (``str``) Prefix designating which battery extract from this file,
                or (``int``) index within the list of available prefixes, sorted alphabetically.
                The default is to read the default prefix (``None``).

        """
        from battdat.io.hdf import HDF5Reader, as_hdf5_object
        reader = HDF5Reader()
        reader.output_class = cls
        with as_hdf5_object(path_or_buf) as store:
            return reader.read_from_hdf(store, prefix, tables)

    @classmethod
    def all_cells_from_hdf(cls, path: Union[str, Path], subsets: Optional[Collection[str]] = None) -> Iterator[Tuple[str, 'CellDataset']]:
        """Iterate over all cells in an HDF file

        Args:
            path: Path to the HDF file
            subsets : Which subsets of data to read from the data file (e.g., raw_data, cycle_stats)
        Yields:
            - Name of the cell
            - Cell data
        """

        # Start by gathering all names of the cells
        _, names = cls.inspect_hdf(path)

        with File(path, mode='r') as fp:  # Only open once
            for name in names:
                yield name, cls.from_hdf(fp, prefix=name, tables=subsets)

    @staticmethod
    def inspect_hdf(path_or_buf: Union[str, Path, File]) -> tuple[BatteryMetadata, Set[Optional[str]]]:
        """Extract the battery data and the prefixes of cells contained within an HDF5 file

        Args:
            path_or_buf: Path to the HDF5 file, or HDFStore object
        Returns:
            - Metadata from this file
            - List of names of batteries stored within the file (prefixes)
        """

        from battdat.io.hdf import inspect_hdf, as_hdf5_object

        with as_hdf5_object(path_or_buf) as store:
            return inspect_hdf(store)

    @staticmethod
    def get_metadata_from_hdf5(path: Union[str, Path]) -> BatteryMetadata:
        """Get battery metadata from an HDF file without reading the data

        Args:
            path: Path to the HDF5 file

        Returns:
            Metadata from this file
        """

        with File(path, 'r') as f:
            return BatteryMetadata.model_validate_json(f.root._v_attrs['metadata'])

    def to_parquet(self, path: Union[Path, str], overwrite: bool = True, **kwargs) -> Dict[str, Path]:
        """Write battery data to a directory of Parquet files

        Keyword arguments are passed to :func:`~pyarrow.parquet.write_table`.

        Args:
            path: Path in which to write to
            overwrite: Whether to overwrite an existing directory
        Returns:
            Map of the name of the subset to
        """
        from battdat.io.parquet import ParquetWriter
        writer = ParquetWriter(overwrite=overwrite, write_options=kwargs)
        return writer.export(self, path)

    @classmethod
    def from_parquet(cls, path: Union[str, Path], subsets: Optional[Collection[str]] = None):
        """Read the battery data from an HDF file

        Args:
            path: Path to a directory containing parquet files
            subsets: Which subsets of data to read from the data file (e.g., raw_data, cycle_stats)
        """
        from battdat.io.parquet import ParquetReader
        reader = ParquetReader()
        reader.output_class = cls
        # Find the parquet files, if no specification is listed
        path = Path(path)
        if subsets is None:
            return reader.read_dataset(path)
        else:
            paths = [path / f'{subset}.parquet' for subset in subsets]
            return reader.read_dataset(paths)

    @staticmethod
    def inspect_parquet(path: Union[str, Path]) -> BatteryMetadata:
        """Get battery metadata from a directory of parquet files without reading them

        Args:
            path: Path to the directory of Parquet files

        Returns:
            Metadata from the files
        """
        from battdat.io.parquet import inspect_parquet_files
        return inspect_parquet_files(path)


class CellDataset(BatteryDataset):
    """Data associated with tests for a single battery cell

    Args:
        metadata: Metadata that describe the battery construction, data provenance and testing routines
        raw_data: Time-series data of the battery state
        cycle_stats: Summaries of each cycle
        eis_data: EIS data taken at multiple times
        schemas: Schemas describing each of the tabular datasets
    """

    @property
    def raw_data(self) -> Optional[pd.DataFrame]:
        """Time-series data capturing the state of the battery as a function of time"""
        return self.tables.get('raw_data')

    @property
    def cycle_stats(self) -> Optional[pd.DataFrame]:
        """Summary statistics of each cycle"""
        return self.tables.get('cycle_stats')

    @property
    def eis_data(self) -> Optional[pd.DataFrame]:
        """Electrochemical Impedance Spectroscopy (EIS) data"""
        return self.tables.get('eis_data')

    def __init__(self,
                 metadata: Union[BatteryMetadata, dict] = None,
                 raw_data: Optional[pd.DataFrame] = None,
                 cycle_stats: Optional[pd.DataFrame] = None,
                 eis_data: Optional[pd.DataFrame] = None,
                 schemas: Optional[Dict[str, ColumnSchema]] = None,
                 tables: Dict[str, pd.DataFrame] = None):
        _schemas = {
            'raw_data': RawData(),
            'cycle_stats': CycleLevelData(),
            'eis_data': EISData()
        }
        if schemas is not None:
            _schemas.update(schemas)

        _datasets = {'raw_data': raw_data, 'eis_data': eis_data, 'cycle_stats': cycle_stats}
        if tables is not None:
            _datasets.update(tables)
        super().__init__(
            tables=_datasets,
            schemas=_schemas,
            metadata=metadata,
        )
