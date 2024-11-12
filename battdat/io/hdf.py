"""Read and write from `battery-data-toolkit's HDF format <https://rovi-org.github.io/battery-data-toolkit/user-guide/formats.html#parquet>`_"""
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional, Union, Tuple, Set, Collection
import warnings

import numpy as np
import pandas as pd
from pandas import HDFStore
from tables import Group, File, Filters, descr_from_dtype, Table

from battdat import __version__
from .base import DatasetWriter, PathLike, DatasetFileReader
from ..data import BatteryDataset
from ..schemas import BatteryMetadata
from ..schemas.column import ColumnSchema


def make_numpy_dtype_from_pandas(df: pd.DataFrame) -> np.dtype:
    """Generate a Numpy dtype from a Pandas dataframe

    Args:
        df: Dataframe to be converted
    Returns:
        - Structured dtype of the data
    """

    # Make the dtype
    output = []
    for name, dtype in df.dtypes.items():
        kind = dtype.kind
        if kind in ['O', 'S', 'U']:
            max_len = df[name].apply(str).apply(len).max()
            output.append((name, np.dtype(f'S{max_len}')))
        elif kind in ['M', 'm', 'V']:
            raise ValueError(f'Data type not supported: {kind}')
        else:
            output.append((name, dtype))
    return np.dtype(output)


def write_df_to_table(file: File, group: Group, name: str, df: pd.DataFrame, filters: Optional[Filters] = None, expected_rows: Optional[int] = None) -> Table:
    """Write a dataframe to an HDF5 file

    Args:
        file: File to be written to
        group: Group which holds the associated datasets
        name: Name of the dataset
        df: DataFrame to write
        filters: Filters to apply to data entering table
        expected_rows:
    Returns:
        Table object holding the dataset
    """

    # Convert the datatype to something HDF5 compatible
    dtype = make_numpy_dtype_from_pandas(df)
    desc, _ = descr_from_dtype(dtype)

    # Make the table then fill
    table = file.create_table(group, name=name, description=desc, expectedrows=len(df), filters=filters)
    row = np.empty((1,), dtype=dtype)  # TODO (wardlt): Consider a batched write (pytables might batch internally)
    for _, df_row in df.iterrows():
        for c in dtype.names:
            row[c] = df_row[c]
        table.append(row)
    return table


def read_df_from_table(table: Table) -> pd.DataFrame:
    """Read a dataframe from a table

    Args:
        table: Table to read from
    Returns:
        Dataframe containing the contents
    """
    array = np.empty((table.nrows,), dtype=table.dtype)
    for i, row in enumerate(table.iterrows()):
        array[i] = row.fetch_all_fields()
    return pd.DataFrame(array)


@contextmanager
def as_hdf5_object(path_or_file: Union[PathLike, File], **kwargs) -> File:
    """Open a path as a PyTables file object if not done already.

    Keyword arguments are used when creating a store from a new file

    Args:
        path_or_file: Either the path to a file or an already open File
            (in which case this function does nothing)
    Yields:
        A file that will close on exit from ``with`` context, if a file was provided.
    """

    if isinstance(path_or_file, PathLike):
        with File(path_or_file, **kwargs) as file:
            yield file
    else:
        yield path_or_file


def inspect_hdf(file: File) -> Tuple[BatteryMetadata, Set[Union[str, None]]]:
    """Gather the metadata describing all datasets and the names of datasets within an HDF5 file

    Args:
        file: HDF5 file to read from

    Returns:
        - Metadata from this file
        - List of names of datasets stored within the file (prefixes)
    """
    # Find all fields
    metadata = BatteryMetadata.model_validate_json(file.root._v_attrs.metadata)  # First char is always "/"

    # Get the names by gathering all names before the "-" in group names
    prefixes = set()
    for group in file.walk_nodes('/', 'Table'):
        prefixes.add(group._v_parent._v_name)
    return metadata, prefixes


class HDF5Reader(DatasetFileReader):
    """Read datasets from a battery-data-toolkit format HDF5 file

    The HDF5 format permits multiple datasets in a single HDF5 file
    so long as they all share the same metadata.

    Access these datasets through the :meth:`read_from_hdf`
    """

    def read_from_hdf(self, file: File, prefix: Union[int, str, None], subsets: Optional[Collection[str]] = None):
        # Determine which group to read from
        if isinstance(prefix, int):
            _, prefixes = inspect_hdf(file)
            prefix = sorted(prefixes)[prefix]
        if prefix is None:
            group = file.root
        else:
            if '/' + prefix not in file:
                raise ValueError(f'No data available for prefix: {prefix}')
            group: Group = file.get_node('/' + prefix)

        # Determine which keys to read
        if subsets is None:
            # Find all datasets which match this prefix
            subsets = [table.name for table in group._f_list_nodes('Table')]  # Get all associated tables
        else:
            not_in = [k for k in subsets if k not in group]
            if len(not_in) > 0:
                raise ValueError(f'File does not contain {len(not_in)} subsets: {", ".join(subsets)}')

        data = {}
        schemas = {}
        for key in subsets:
            table = group[key]
            data[key] = read_df_from_table(table)
            schemas[key] = ColumnSchema.from_json(table.attrs.metadata)

        # If no data with this prefix is found, report which ones are found in the file
        if len(data) == 0:
            raise ValueError(f'No data available for prefix "{prefix}". '
                             'Call `BatteryDataset.inspect_hdf` to gather a list of available prefixes.')

        # Read out the battery metadata
        metadata = BatteryMetadata.model_validate_json(file.root._v_attrs.metadata)
        return self.output_class(metadata=metadata, datasets=data, schemas=schemas)

    def read_dataset(self, path: PathLike, metadata: Optional[Union[BatteryMetadata, dict]] = None) -> BatteryDataset:
        """Read the default dataset and all subsets from an HDF5 file

        Use :meth:`read_from_hdf` for more control over reads.

        Args:
            path: Path to the HDF file
            metadata: Metadata to use in place of any found in the file
        Returns:
            Dataset read from the file
        """
        with HDFStore(path) as store:
            data = self.read_from_hdf(store, prefix=None)
            if metadata is not None:
                data.metadata = metadata
            return data


@dataclass
class HDF5Writer(DatasetWriter):
    """Interface to write HDF5 files in battery-data-toolkit's layout

    The :meth:`write_to_hdf` method writes a dataset file with the default settings:
    assuming a single dataset per HDF5 file.

    Use :meth:`write_to_hdf` to store multiple datasets in the file
    with a different "prefix" for each.
    """

    complevel: int = 0
    """Compression level for data. A value of 0 disables compression."""
    complib: str = 'zlib'
    """Specifies the compression library to be used."""

    def write_to_hdf(self, dataset: BatteryDataset, file: File, prefix: Optional[str]):
        """Add a dataset to an already-open HDF5 file

        Args:
            dataset: Dataset to be added
            file: PyTables file object in which to save the data
            prefix: Prefix used when storing the data. Use prefixes to store multiple cells in the same HDF5
        """

        # Write the metadata to the file-level attributes (those of the root group)
        metadata = dataset.metadata.model_dump_json()
        root_node = file.get_node('/')
        if 'metadata' in root_node._v_attrs:
            existing_metadata = root_node._f_getattr('metadata')
            if metadata != existing_metadata:
                warnings.warn('Metadata already in HDF5 differs from new metadata')
        root_node._f_setattr('metadata', metadata)
        root_node._f_setattr('json_schema', dataset.metadata.model_json_schema())
        root_node._f_setattr('battdat_version', __version__)

        # Move to the group in which to store the data
        if prefix is not None:
            group: Group = file.create_group('/', name=prefix)
        else:
            group = file.root

        # Store the various datasets
        #  Note that we use the "table" format to allow for partial reads / querying
        filters = Filters(complevel=self.complevel, complib=self.complib)
        for key, schema in dataset.schemas.items():
            if (data := dataset.datasets.get(key)) is not None:
                table = write_df_to_table(file, group, key, data, filters=filters)

                # Write the schema, mark as dataset
                table.attrs.metadata = schema.model_dump_json()
                table.attrs.json_schema = schema.model_dump_json()

    def export(self, dataset: BatteryDataset, path: PathLike):
        with File(path, mode='w') as file:
            self.write_to_hdf(dataset, file, prefix=None)
