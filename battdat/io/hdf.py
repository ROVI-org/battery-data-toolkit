"""Read and write from `battery-data-toolkit's HDF format <https://rovi-org.github.io/battery-data-toolkit/user-guide/formats.html#parquet>`_"""
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional, Union, Tuple, Set, Collection
import warnings

from pydantic import BaseModel
from pandas import HDFStore
from tables import Group

from .base import DatasetWriter, PathLike, DatasetFileReader
from ..data import BatteryDataset
from ..schemas import BatteryMetadata
from ..schemas.column import ColumnSchema


@contextmanager
def as_hdf5_store(path_or_store: Union[PathLike, HDFStore], **kwargs) -> HDFStore:
    """Provide an HDF5Store interface to a file

    Keyword arguments are used when creating a store from a new file

    Args:
        path_or_store: Either the path to a file or an already open store
            (in which case this function does nothing)
    Yields:
        A store that will close on exit from ``with`` context only, if a file was provided.
    """

    if isinstance(path_or_store, PathLike):
        with HDFStore(path_or_store, **kwargs) as store:
            yield store
    else:
        yield path_or_store


def inspect_hdf(store: HDFStore) -> Tuple[BatteryMetadata, Set[Union[str, None]]]:
    """Gather the metadata describing all datasets and the names of datasets within an HDF5 file

    Args:
        store: HDF5Store to be read from

    Returns:
        - Metadata from this file
        - List of names of datasets stored within the file (prefixes)
    """
    # Find all fields
    metadata = BatteryMetadata.model_validate_json(store.root._v_attrs.metadata)  # First char is always "/"

    # Get the names by gathering all names before the "-" in group names
    prefixes = set()
    for key in store.keys():
        # Skip keys which don't correspond to dataset
        group = store.root[key]
        if hasattr(group._v_attrs, 'battdat_type') and group._v_attrs.battdat_type == 'subset':
            names = key[1:].rsplit("/", 1)  # Last is dataset name, previous is key to
            prefixes.add('' if len(names) == 1 else names[0])
    return metadata, prefixes


class HDF5Reader(DatasetFileReader):
    """Read datasets from a battery-data-toolkit format HDF5 file

    The HDF5 format permits multiple datasets in a single HDF5 file
    so long as they all share the same metadata.

    Access these datasets through the :meth:`read_from_hdf`
    """

    def read_from_hdf(self, store: HDFStore, prefix: Union[int, str, None], subsets: Optional[Collection[str]] = None):
        if isinstance(prefix, int):
            _, prefixes = inspect_hdf(store)
            prefix = sorted(prefixes)[prefix]

        # Determine which keys to read
        keys_to_read = []
        read_all = subsets is None
        if subsets is None:
            # Find all datasets which match this prefix
            for key in store.keys():
                # Skip keys which are not battdat subsets
                group = store.root[key]
                if not (hasattr(group._v_attrs, 'battdat_type') and group._v_attrs.battdat_type == 'subset'):
                    continue

                # Skip ones that don't belong to this dataset
                if prefix is None and key.count('/') == 1:
                    keys_to_read.append(key)
                elif key.startswith(f'/{prefix}/'):
                    keys_to_read.append(key)
        else:
            # Make the expected keys
            for subset in subsets:
                keys_to_read.append(subset if prefix is None else f'{prefix}/{subset}')

        data = {}
        schemas = {}
        for key in keys_to_read:
            subset = key.rsplit("/", maxsplit=1)[-1]
            try:
                data[subset] = store.get(key)
            except KeyError as exc:
                if read_all:
                    continue
                else:
                    raise ValueError(f'File does not contain {key}') from exc

            # Read the schema
            group = store.root[key]
            schemas[subset] = ColumnSchema.from_json(group._v_attrs.metadata)

        # If no data with this prefix is found, report which ones are found in the file
        if len(data) == 0:
            raise ValueError(f'No data available for prefix "{prefix}". '
                             'Call `BatteryDataset.inspect_hdf` to gather a list of available prefixes.')

        # Read out the battery metadata
        metadata = BatteryMetadata.model_validate_json(store.root._v_attrs.metadata)
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

    def write_to_hdf(self, dataset: BatteryDataset, store: HDFStore, prefix: Optional[str]):
        """Add a dataset to an already-open HDF5 file

        Args:
            dataset: Dataset to be added
            store: HDF5Store used to write the data
            prefix: Prefix used when storing the data. Use prefixes to store multiple cells in the same HDF5
        """

        # Create logic for adding metadata
        def add_metadata(f: Group, m: BaseModel):
            """Put the metadata in a standard location at the root of the HDF file"""
            metadata = m.model_dump_json()
            if 'metadata' in f._v_attrs:
                existing_metadata = f._v_attrs.metadata
                if metadata != existing_metadata:
                    warnings.warn('Metadata already in HDF5 differs from new metadata')
            f._v_attrs.metadata = metadata
            f._v_attrs.json_schema = m.model_json_schema()

        # Store the various datasets
        #  Note that we use the "table" format to allow for partial reads / querying
        for key, schema in dataset.schemas.items():
            if (data := dataset.datasets.get(key)) is not None:
                if prefix is not None:
                    key = f'{prefix}/{key}'
                data.to_hdf(store,
                            key=key,
                            complevel=self.complevel,
                            complib=self.complib,
                            append=False,
                            format='table',
                            index=False)

                # Write the schema, mark as dataset
                add_metadata(store.root[key], schema)
                store.root[key]._v_attrs.battdat_type = 'subset'

        # Store the high-level metadata
        add_metadata(store.root, dataset.metadata)
        group = store.root if prefix is None else store.root[prefix]
        group._v_attrs.battdat_type = 'dataset'

    def export(self, dataset: BatteryDataset, path: PathLike):

        with HDFStore(path, complevel=self.complevel, complib=self.complib) as store:
            self.write_to_hdf(dataset, store, prefix=None, append=False)
