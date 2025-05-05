"""Retrieve data in smaller chunks from a large HDF5 file"""
from itertools import groupby
from pathlib import Path
from typing import Union, Iterator, Dict, List

import numpy as np
import pandas as pd
from pandas import HDFStore
from tables import File, Table

from battdat.data import BatteryDataset
from battdat.io.hdf import as_hdf5_object


def _get_raw_data_iterator_h5(hdf5_path: Union[Path, str, File], key: str) -> Iterator[np.ndarray]:
    """Open an iterator over rows of an HDF5 Table"""

    with as_hdf5_object(hdf5_path) as file:
        table: Table = file.get_node(key)
        names = table.dtype.fields.keys()
        for row in table.iterrows():
            out = dict((n, row[n]) for n in names)
            yield out


def iterate_records_from_file(hdf5_path: Union[Path, str, HDFStore], key: str = '/raw_data') -> Iterator[Dict[str, Union[str, float, int]]]:
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
                             key: str = '/raw_data') -> Iterator[Union[pd.DataFrame, BatteryDataset]]:
    """Stream single-cycle datasets from the HDF5 file

    Args:
        hdf5_path: Path to the data file
        make_dataset: Whether to form a :class:`~battdat.data.BatteryDataset` for each cycle,
            including the metadata from the source file.
        key: Which table to read

    Yields:
        All rows belonging to each cycle from the "raw_data" section fo the HDF5 file.
    """

    # Get the metadata out of the file, if needed
    metadata = None
    if make_dataset:
        metadata, _ = BatteryDataset.inspect_hdf(hdf5_path)

    def _assemble_from_records(chunks: List[dict]):
        combined = pd.DataFrame(chunks)
        if make_dataset:
            return BatteryDataset.make_cell_dataset(metadata=metadata, raw_data=combined)
        return combined

    for _, chunk in groupby(_get_raw_data_iterator_h5(hdf5_path, key), lambda x: x['cycle_number']):
        yield _assemble_from_records(chunk)
