"""Read and write from `battery-data-toolkit's parquet format <https://rovi-org.github.io/battery-data-toolkit/user-guide/formats.html#parquet>`_"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, Union, Collection
from pathlib import Path
import warnings
import logging
import shutil

from pyarrow import parquet as pq
from pyarrow import Table

from .base import DatasetWriter, DatasetFileReader, PathLike
from ..data import BatteryDataset
from ..schemas import BatteryMetadata
from ..schemas.column import ColumnSchema

logger = logging.getLogger(__name__)


def inspect_parquet_files(path: PathLike) -> BatteryMetadata:
    """Read the metadata from a collection of Parquet files

    Args:
        path: Path to a directory of parquet files

    Returns:
        Metadata from one of the files
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


@dataclass
class ParquetWriter(DatasetWriter):
    """Write to parquet files in the format specification of battery-data-toolkit

    Writes all data to the same directory with a separate parquet file for each table.
    The battery metadata, column schemas, and write date are all saved in the file-level metadata for each file.
    """

    overwrite: bool = False
    """Whether to overwrite existing data"""
    write_options: Dict[str, Any] = field(default_factory=dict)
    """Options passed to :func:`~pyarrow.parquet.write_table`."""

    def export(self, dataset: BatteryDataset, path: Path):
        # Handle existing paths
        path = Path(path)
        if path.exists():
            if not self.overwrite:
                raise ValueError(f'Path already exists and overwrite is disabled: {path}')
            logger.info(f'Deleting existing directory at {path}')
            shutil.rmtree(path)

        # Make the output directory, then write each Parquet file
        path.mkdir(parents=True, exist_ok=False)
        my_metadata = {
            'battery_metadata': dataset.metadata.model_dump_json(exclude_none=True),
            'write_date': datetime.now().isoformat()
        }
        written = {}
        for key, schema in dataset.schemas.items():
            if (data := dataset.datasets.get(key)) is None:
                continue

            # Put the metadata for the battery and this specific table into the table's schema in the FileMetaData
            data_path = path / f'{key}.parquet'
            my_metadata['table_metadata'] = schema.model_dump_json()
            table = Table.from_pandas(data, preserve_index=False)
            new_schema = table.schema.with_metadata({**my_metadata, **table.schema.metadata})
            table = table.cast(new_schema)
            pq.write_table(table, where=data_path, **self.write_options)

            written[key] = data_path
        return written


class ParquetReader(DatasetFileReader):
    """Read parquet files formatted according to battery-data-toolkit standards

    Mirrors :class:`ParquetWriter`. Expects each constituent table to be in a separate parquet
    file and to have the metadata stored in the file-level metadata of the parquet file.
    """

    def read_dataset(self, paths: Union[PathLike, Collection[PathLike]], metadata: Optional[Union[BatteryMetadata, dict]] = None) -> BatteryDataset:
        """Read a set of parquet files into a BatteryDataset

        Args:
            paths: Either the path to a single-directory of files, or a list of files to parse
            metadata: Metadata which will overwrite what is available in the files

        Returns:
            Dataset including all subsets
        """
        # Find the parquet files, if no specification is listed
        if isinstance(paths, PathLike):
            paths = [paths]
        paths = [Path(p) for p in paths]
        if len(paths) == 1 and paths[0].is_dir():
            paths = list(paths[0].glob('*.parquet'))
        elif not all(is_file := [p.is_file() for p in paths]):
            not_files = [p for i, p in zip(is_file, paths) if not i]
            raise ValueError(f'Expected either a list of files or a single directory. The following are not files: {not_files}')

        if len(paths) == 0 and metadata is None:
            raise ValueError('No data available.')

        # Load each subset
        metadata = None
        data = {}
        schemas = {}
        for data_path in paths:
            subset = data_path.with_suffix('').name
            table = pq.read_table(data_path)

            # Load or check the metadata
            if b'battery_metadata' not in table.schema.metadata:
                warnings.warn(f'Battery metadata not found in {data_path}')
            else:
                # Load the metadata for the whole cell
                my_metadata = table.schema.metadata[b'battery_metadata'] if metadata is None else metadata
                if metadata is None:
                    metadata = my_metadata
                elif my_metadata != metadata:
                    warnings.warn(f'Battery data different for files in {data_path}')

            # Load the batdata schema for the table
            if b'table_metadata' not in table.schema.metadata:
                warnings.warn(f'Column schema not found in {data_path}')
            schemas[subset] = ColumnSchema.from_json(table.schema.metadata[b'table_metadata'])

            # Read it to a dataframe
            data[subset] = table.to_pandas()

        return self.output_class(
            metadata=BatteryMetadata.model_validate_json(metadata),
            schemas=schemas,
            datasets=data
        )
