"""Retrieve data in smaller chunks from a large HDF5 file"""
from pathlib import Path
from contextlib import contextmanager
from typing import Union, Iterator, Dict, List

import pandas as pd
from pandas import HDFStore
from pandas.io.pytables import TableIterator

from battdat.data import BatteryDataset


@contextmanager
def _get_raw_data_iterator_h5(hdf5_path: Union[Path, str, HDFStore], **kwargs) -> Iterator[pd.DataFrame]:
    """Open an iterator over chunks of an HDF5 file"""
    chunk_iter: TableIterator = pd.read_hdf(hdf5_path, key='raw_data', iterator=True, **kwargs)
    try:
        yield chunk_iter
    finally:
        if not isinstance(hdf5_path, HDFStore):
            chunk_iter.close()


def iterate_records_from_file(hdf5_path: Union[Path, str, HDFStore], **kwargs) -> Iterator[Dict[str, Union[str, float, int]]]:
    """Stream individual records from a file

    Keyword arguments are passed to :meth:`~pandas.read_hdf`, which includes options
    to limit which rows and columns are read.

    Args:
        hdf5_path: Path to the data file

    Yields:
        Individual rows from the "raw_data" section of the HDF5 file
    """

    with _get_raw_data_iterator_h5(hdf5_path, **kwargs) as chunk_iter:
        for chunk in chunk_iter:
            for _, row in chunk.iterrows():
                yield row


def iterate_cycles_from_file(hdf5_path: Union[Path, str, HDFStore],
                             make_dataset: bool = False,
                             **kwargs) -> Iterator[Union[pd.DataFrame, BatteryDataset]]:
    """Stream single-cycle datasets from the HDF5 file

    Keyword arguments are passed to :meth:`~pandas.read_hdf`, which includes options
    to limit which rows and columns are read.

    Args:
        hdf5_path: Path to the data file
        make_dataset: Whether to form a :class:`~battdat.data.BatteryDataset` for each cycle,
            including the metadata from the source file.

    Yields:
        All rows belonging to each cycle from the "raw_data" section fo the HDF5 file.
    """

    # Get the metadata out of the file, if needed
    metadata = None
    if make_dataset:
        metadata, _ = BatteryDataset.inspect_hdf(hdf5_path)

    def _assemble_from_chunks(chunks: List[pd.DataFrame]):
        combined = pd.concat(chunks)
        if make_dataset:
            return BatteryDataset(metadata=metadata, raw_data=combined)
        return combined

    current_cycle = None
    current_cycle_chunks = None
    with _get_raw_data_iterator_h5(hdf5_path, **kwargs) as chunk_iter:
        for new_chunk in chunk_iter:  # Until no more data
            while not (cycle_mask := new_chunk['cycle_number'] == current_cycle).all():  # Loop until only current cycle
                my_cycle = new_chunk[cycle_mask]  # Retrieve the parts from the current cycle
                new_chunk = new_chunk[~cycle_mask]  # Remove those parts from the current chunk

                # Yield the current data then reset the collection, increment cycle tracker
                if current_cycle_chunks is not None:
                    current_cycle_chunks.append(my_cycle)
                    yield _assemble_from_chunks(current_cycle_chunks)
                current_cycle_chunks = []
                current_cycle = new_chunk['cycle_number'].iloc[0]
            current_cycle_chunks.append(new_chunk)

    yield _assemble_from_chunks(current_cycle_chunks)
