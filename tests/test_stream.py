"""Evaluate streaming reads from files"""
from itertools import zip_longest
from pathlib import Path

import numpy as np
from tables import File
from pytest import fixture, mark, raises

from battdat.data import BatteryDataset
from battdat.io.batterydata import BDReader
from battdat.postprocess.timing import CycleTimesSummarizer
from battdat.streaming import iterate_records_from_file, iterate_cycles_from_file
from battdat.streaming.hdf5 import HDF5Writer


@fixture()
def example_dataset(file_path):
    data = BDReader().read_dataset([file_path / 'batterydata' / 'p492-13-raw.csv'])
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
    test_data = BatteryDataset.from_hdf(example_h5_path)
    cycle_iter = iterate_cycles_from_file(example_h5_path)
    for streamed, (_, original) in zip_longest(cycle_iter, test_data.raw_data.groupby('cycle_number')):
        assert streamed is not None
        assert original is not None
        assert np.allclose(streamed['test_time'], original['test_time'])

    # Test reading a list of keys
    cycle_iter = iterate_cycles_from_file(example_h5_path, make_dataset=False, key=['raw_data'])
    cycle_0 = next(cycle_iter)
    assert 'raw_data' in cycle_0

    # Ensure we can generate chunks with metadata
    for key in ('raw_data', ['raw_data']):
        cycle_iter = iterate_cycles_from_file(example_h5_path, make_dataset=True, key=key)
        cycle_0 = next(cycle_iter)
        assert cycle_0.metadata == test_data.metadata


def test_stream_by_cycles_with_stats(example_dataset, tmpdir):
    # Remove EIS data, add capacities
    example_dataset.tables.pop('eis_data')
    CycleTimesSummarizer().add_summaries(example_dataset)
    assert 'cycle_stats' in example_dataset
    h5_path = Path(tmpdir / 'test.h5')
    example_dataset.to_hdf(h5_path)

    # Test streaming a cycle
    cycle_iter = iterate_cycles_from_file(h5_path, make_dataset=False, key=None)
    cycle_0 = next(cycle_iter)
    assert cycle_0['cycle_stats'].iloc[0]['cycle_number'] == 0

    # Delete the first row in the cycle steps to cause an error
    example_dataset.cycle_stats.drop(index=0, inplace=True)
    h5_path = Path(tmpdir / 'test-fail.h5')
    example_dataset.to_hdf(h5_path)

    cycle_iter = iterate_cycles_from_file(h5_path, make_dataset=False, key=None)
    with raises(ValueError, match='cycle_stats=1'):
        next(cycle_iter)


@mark.parametrize('buffer_size', [128, 400000000])  # Way smaller than data size, way larger
def test_streaming_write(example_dataset, buffer_size, tmpdir):
    out_file = Path(tmpdir) / 'streamed.h5'
    writer = HDF5Writer(out_file, metadata=example_dataset.metadata, buffer_size=buffer_size)
    assert len(example_dataset.raw_data) > 0
    with writer:
        for _, row in example_dataset.raw_data.iterrows():
            writer.write_row(row.to_dict())

    # Make sure the data are identical
    copied_data = BatteryDataset.from_hdf(out_file)
    assert copied_data.metadata.name == example_dataset.metadata.name
    cols = ['test_time', 'current']
    assert np.allclose(copied_data.raw_data[cols], example_dataset.raw_data[cols])


def test_streaming_write_existing_store(example_dataset, tmpdir):
    out_file = Path(tmpdir) / 'streamed.h5'
    with File(out_file, mode='a') as file, HDF5Writer(file, buffer_size=2, complevel=4) as writer:
        assert writer.write_row({'test_time': 0.}) == 0  # Written on close, so the number written here is zero

    with File(out_file, mode='a') as file, HDF5Writer(file, buffer_size=2, complevel=4) as writer:
        assert writer.write_row({'test_time': 1.}) == 0

    # Read it in
    data = BatteryDataset.from_hdf(out_file)
    assert np.allclose(data.raw_data['test_time'], [0., 1.])
