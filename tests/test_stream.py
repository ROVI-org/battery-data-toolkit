"""Evaluate streaming reads from files"""
from itertools import zip_longest
from pathlib import Path

import numpy as np
import pandas as pd
from pytest import fixture, mark

from battdat.data import CellDataset
from battdat.io.batterydata import BDExtractor
from battdat.streaming import iterate_records_from_file, iterate_cycles_from_file
from battdat.streaming.hdf5 import HDF5Writer


@fixture()
def example_dataset(file_path):
    data = BDExtractor().read_dataset([file_path / 'batterydata' / 'p492-13-raw.csv'])
    data.metadata.name = 'test_name'
    return data


@fixture()
def example_h5_path(tmpdir, example_dataset):
    h5_path = Path(tmpdir) / 'example_h5'
    example_dataset.to_hdf(h5_path)
    return h5_path


def test_stream_by_rows(example_h5_path):
    row_iter = iterate_records_from_file(example_h5_path)

    row_0 = next(row_iter)
    assert row_0['test_time'] == 0.
    row_1 = next(row_iter)
    assert row_1['voltage'] == 3.27191577


def test_stream_by_cycles(example_h5_path):
    test_data = CellDataset.from_hdf(example_h5_path)
    cycle_iter = iterate_cycles_from_file(example_h5_path, chunksize=4)  # Small to make sure we split cycles across chunks
    for streamed, (_, original) in zip_longest(cycle_iter, test_data.raw_data.groupby('cycle_number')):
        assert streamed is not None
        assert original is not None
        assert np.allclose(streamed['test_time'], original['test_time'])

    # Ensure we can generate chunks with metadata
    cycle_iter = iterate_cycles_from_file(example_h5_path, make_dataset=True)
    cycle_0 = next(cycle_iter)
    assert cycle_0.metadata == test_data.metadata


@mark.parametrize('buffer_size', [128, 400000000])  # Way smaller than data size, way larger
def test_streaming_write(example_dataset, buffer_size, tmpdir):
    out_file = Path(tmpdir) / 'streamed.h5'
    writer = HDF5Writer(out_file, metadata=example_dataset.metadata, buffer_size=buffer_size)
    assert len(example_dataset.raw_data) > 0
    with writer:
        for _, row in example_dataset.raw_data.iterrows():
            writer.write_row(row.to_dict())

    # Make sure the data are identical
    copied_data = CellDataset.from_hdf(out_file)
    assert copied_data.metadata.name == example_dataset.metadata.name
    cols = ['test_time', 'current']
    assert np.allclose(copied_data.raw_data[cols], example_dataset.raw_data[cols])


def test_streaming_write_existing_store(example_dataset, tmpdir):
    out_file = Path(tmpdir) / 'streamed.h5'
    with pd.HDFStore(out_file) as store, HDF5Writer(store, buffer_size=2, complevel=4) as writer:
        assert writer.write_row({'test_time': 0.}) == 0
        assert writer.write_row({'test_time': 1.}) == 2

    # Read it in
    data = CellDataset.from_hdf(out_file)
    assert np.allclose(data.raw_data['test_time'], [0., 1.])
