"""Retrieve data in smaller chunks from a large HDF5 file"""
from pathlib import Path
from typing import Union, Iterator, Dict

import pandas as pd
from pandas import HDFStore
from pandas.io.pytables import TableIterator


def iterate_records_from_file(hdf5_path: Union[Path, str, HDFStore], **kwargs) -> Iterator[Dict[str, Union[str, float, int]]]:
    """Stream individual records from a file

    Keyword arguments are passed to :meth:`~pandas.read_hdf`.

    Args:
        hdf5_path: Path to the data file

    Yields:
        Individual rows from the "time-series"
    """

    chunk_iter: TableIterator = pd.read_hdf(hdf5_path, key='raw_data', iterator=True, **kwargs)
    try:
        for chunk in chunk_iter:
            for _, row in chunk.iterrows():
                yield row.to_dict()
    finally:
        if not isinstance(hdf5_path, HDFStore):
            chunk_iter.close()
