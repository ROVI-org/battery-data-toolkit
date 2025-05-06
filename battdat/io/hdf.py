"""Read and write from `battery-data-toolkit's HDF format <https://rovi-org.github.io/battery-data-toolkit/user-guide/formats.html#hdf5>`_"""
from typing import Optional, Union, Tuple, Set, Collection, Dict
from contextlib import contextmanager
from dataclasses import dataclass
from json import JSONDecodeError
import warnings

import numpy as np
import pandas as pd
from tables import Group, File, Filters, descr_from_dtype, Table
from pydantic import ValidationError

from battdat import __version__
from .base import DatasetWriter, PathLike, DatasetReader
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
        shape = ()

        # Introspect objects to learn more
        if kind == 'O':
            example = np.array(df[name].iloc[0])
            dtype = example.dtype
            kind = dtype.kind
            shape = example.shape

        if kind in ['S', 'U']:
            max_len = df[name].apply(str).apply(len).max()
            output.append((name, np.dtype(f'S{max_len}')))
        elif kind in ['M', 'm', 'V']:
            raise ValueError(f'Data type not supported: {kind}')
        else:
            output.append((name, dtype, shape))
    return np.dtype(output)


def write_df_to_table(file: File, group: Group, name: str, df: pd.DataFrame, filters: Optional[Filters] = None, expected_rows: Optional[int] = None) -> Table:
    """Write a dataframe to an HDF5 file

    Args:
        file: File to be written to
        group: Group which holds the associated datasets
        name: Name of the dataset
        df: DataFrame to write
        filters: Filters to apply to data entering table
        expected_rows: How many rows to expect. Default is to use the length of the dataframe
    Returns:
        Table object holding the dataset
    """

    # Convert the datatype to something HDF5 compatible
    dtype = make_numpy_dtype_from_pandas(df)
    desc, _ = descr_from_dtype(dtype)

    # Make the table then fill
    table = file.create_table(group, name=name, description=desc, expectedrows=expected_rows or len(df), filters=filters)
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
    as_dict = dict((c, array[c]) for c in array.dtype.names)

    # Expand ndarrays into a list
    for k, v in as_dict.items():
        if v.ndim != 1:
            as_dict[k] = list(v)
    return pd.DataFrame(as_dict)


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


def inspect_hdf(file: File) -> Tuple[BatteryMetadata, Set[Union[str, None]], Dict[str, ColumnSchema]]:
    """Gather the metadata describing all datasets and the names of datasets within an HDF5 file

    Args:
        file: HDF5 file to read from

    Returns:
        - Metadata from this file
        - List of names of datasets stored within the file (prefixes)
    """
    # Find all fields
    metadata = BatteryMetadata.model_validate_json(file.root._v_attrs.metadata)

    # Get the names by gathering all names before the "-" in group names
    prefixes = set()
    schema_json = dict()
    for group in file.walk_nodes('/', 'Table'):
        # Store the prefix name
        prefix = group._v_parent._v_name
        prefixes.add(prefix)

        # Load the schema
        table_name = group._v_name
        table_schema = group._v_attrs.metadata
        if table_name in schema_json and table_schema != schema_json[table_name]:
            warnings.warn(f'Schema of table {prefix}/{table_name} does not match others')
        schema_json[table_name] = table_schema

    # Convert the schema from JSON to objects
    schemas = dict((k, ColumnSchema.from_json(v)) for k, v in schema_json.items())
    return metadata, prefixes, schemas


class HDF5Reader(DatasetReader):
    """Read datasets from a battery-data-toolkit format HDF5 file

    The HDF5 format permits multiple datasets in a single HDF5 file
    so long as they all share the same metadata.

    Access these datasets through the :meth:`read_from_hdf`
    """

    def read_from_hdf(self, file: File, prefix: Union[int, str, None], subsets: Optional[Collection[str]] = None):
        # Determine which group to read from
        if isinstance(prefix, int):
            _, prefixes, _ = inspect_hdf(file)
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
            try:
                schemas[key] = ColumnSchema.from_json(table._v_attrs.metadata)
            except (AttributeError, JSONDecodeError, ValidationError) as e:
                # TODO (wardlt): Once our format settles, only bother parsing tables with `battdat_version` attr
                if 'battdat_version' in table._v_attrs:
                    raise ValueError(f'Table {key} is marked as a battdat dataset but schema fails to read') from e
                else:
                    continue
            data[key] = read_df_from_table(table)

        # If no data with this prefix is found, report which ones are found in the file
        if len(data) == 0:
            raise ValueError(f'No data available for prefix "{prefix}". '
                             'Call `BatteryDataset.inspect_hdf` to gather a list of available prefixes.')

        # Read out the battery metadata
        metadata = BatteryMetadata.model_validate_json(file.root._v_attrs.metadata)
        return BatteryDataset.make_cell_dataset(metadata=metadata, tables=data, schemas=schemas)

    def read_dataset(self, path: PathLike, metadata: Optional[Union[BatteryMetadata, dict]] = None) -> BatteryDataset:
        """Read the default dataset and all subsets from an HDF5 file

        Use :meth:`read_from_hdf` for more control over reads.

        Args:
            path: Path to the HDF file
            metadata: Metadata to use in place of any found in the file
        Returns:
            Dataset read from the file
        """
        with File(path) as file:
            data = self.read_from_hdf(file, prefix=None)
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

        # Create the group if needed
        if prefix is not None:
            file.create_group('/', name=prefix)

        # Store the various datasets
        #  Note that we use the "table" format to allow for partial reads / querying
        for key, schema in dataset.schemas.items():
            if (data := dataset.tables.get(key)) is not None:
                self.add_table(file, key, data, schema, prefix)

    def add_table(self, file: File, name: str, data: pd.DataFrame, schema: ColumnSchema, prefix: Optional[str] = None):
        """Add a table to an existing dataset

        Args:
            file: HDF file open via pytables
            name: Name of the data table
            data: Data table to be saved
            schema: Description of the columns in battdat format
            prefix: Prefix of the battery dataset if saving multiple per file
        """
        # Write dataset
        group = file.root if prefix is None else file.get_node('/' + prefix)
        filters = Filters(complevel=self.complevel, complib=self.complib)
        table = write_df_to_table(file, group, name, data, filters=filters)

        # Write the schema, mark as dataset
        table.attrs.battdat_version = __version__
        table.attrs.metadata = schema.model_dump_json()
        table.attrs.json_schema = schema.model_json_schema()

    def append_to_table(self, file: File, name: str, data: pd.DataFrame, prefix: Optional[str] = None):
        """Add to an existing table

        Args:
            file: HDF file open via pytables
            name: Name of the data table
            data: Data table to be saved
            prefix: Prefix of the battery dataset if saving multiple per file
        """

        # Get the table
        if prefix is None:
            group = file.root
        else:
            if '/' + prefix not in file:
                raise ValueError(f'No data available for prefix: {prefix}')
            group: Group = file.get_node('/' + prefix)
        table: Table = group[name]

        # Check tables
        new_dtype = make_numpy_dtype_from_pandas(data)
        cur_dtype = table.dtype
        if new_dtype != cur_dtype:
            raise ValueError(f'Existing and new data types differ. Existing={cur_dtype}, New={new_dtype}')

        row = np.empty((1,), dtype=cur_dtype)  # TODO (wardlt): Consider a batched write (pytables might batch internally)
        for _, df_row in data.iterrows():
            for c in cur_dtype.names:
                row[c] = df_row[c]
            table.append(row)

    def export(self, dataset: BatteryDataset, path: PathLike):
        with File(path, mode='w') as file:
            self.write_to_hdf(dataset, file, prefix=None)
