"""Retrieve data in smaller chunks from a large HDF5 file"""
from typing import Union, Iterator, Dict, Collection
from itertools import groupby
from pathlib import Path

import pandas as pd
from pandas import HDFStore
from tables import File, Table

from battdat.data import BatteryDataset
from battdat.io.hdf import as_hdf5_object

RecordType = Dict[str, Union[str, float, int]]


def _get_raw_data_iterator_h5(hdf5_path: Union[Path, str, File], key: str) -> Iterator[RecordType]:
    """Open an iterator over rows of an HDF5 Table"""

    with as_hdf5_object(hdf5_path) as file:
        table: Table = file.get_node(f'/{key}')
        names = table.dtype.fields.keys()
        for row in table.iterrows():
            out = dict((n, row[n]) for n in names)
            yield out


def iterate_records_from_file(hdf5_path: Union[Path, str, HDFStore], key: str = 'raw_data') -> Iterator[RecordType]:
    """Stream individual records from a file

    Args:
        hdf5_path: Path to the data file
        key: Which table to read
    Yields:
        Individual rows from the "raw_data" section of the HDF5 file
    """

    yield from _get_raw_data_iterator_h5(hdf5_path, key=key)


def iterate_cycles_from_file(hdf5_path: Union[Path, str, HDFStore],
                             make_dataset: bool = False,
                             key: str | Collection[str] | None = 'raw_data') -> Iterator[Union[pd.DataFrame, Dict[str, pd.DataFrame], BatteryDataset]]:
    """Stream single-cycle datasets from the HDF5 file

    Args:
        hdf5_path: Path to the data file
        make_dataset: Whether to form a :class:`~battdat.data.BatteryDataset` for each cycle,
            including the metadata from the source file.
        key: Which table(s) to read. Supply either a single key, a list of keys, or ``None`` to read all tables

    Yields:
        All rows belonging to each cycle from the requested table of the HDF5 file.
        Generates a ``BatteryDataset`` if ``make_dataset`` is ``True``.
        Otherwise, yields a single DataFrame if ``key`` is a single string
        or a dictionary of DataFrames if ``key`` is a list.
    """

    # Get the metadata out of the file, if needed
    metadata = None
    if make_dataset or key is None:
        metadata, _, schemas = BatteryDataset.inspect_hdf(hdf5_path)

    # Determine the keys to read from the file
    single = False
    if isinstance(key, str):
        single = True
        keys = [key]
    elif key is None:
        keys = list(schemas.keys())
    else:
        keys = list(key)

    iterators = [
        groupby(_get_raw_data_iterator_h5(hdf5_path, k), lambda x: x['cycle_number']) for k in keys
    ]

    for batch in zip(*iterators):
        cycle_ids, chunks = zip(*batch)
        if len(set(cycle_ids)) != 1:
            raise ValueError(f'Different cycle indices across entries: {" ".join(f"{k}={i}" for k, i in zip(keys, cycle_ids))}')

        # Produce the desired output file
        chunks = [pd.DataFrame(chunk) for chunk in chunks]
        if single and not make_dataset:
            yield chunks[0]
        elif make_dataset:
            yield BatteryDataset(
                metadata=metadata,
                schemas=schemas,
                tables=dict(zip(keys, chunks))
            )
        else:
            yield dict(zip(keys, chunks))
