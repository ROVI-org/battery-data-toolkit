"""Evaluate streaming reads from files"""
from itertools import zip_longest
from pathlib import Path

import numpy as np
from pytest import fixture

from batdata.data import BatteryDataset
from batdata.extractors.batterydata import BDExtractor
from batdata.streaming import iterate_records_from_file, iterate_cycles_from_file


@fixture()
def example_h5_path(tmpdir, file_path):
    data = BDExtractor().parse_to_dataframe([file_path / 'batterydata' / 'p492-13-raw.csv'])
    h5_path = Path(tmpdir) / 'example_h5'
    data.to_batdata_hdf(h5_path)
    return h5_path


def test_stream_by_rows(example_h5_path):
    row_iter = iterate_records_from_file(example_h5_path)

    row_0 = next(row_iter)
    assert row_0['test_time'] == 0.
    row_1 = next(row_iter)
    assert row_1['voltage'] == 3.27191577


def test_stream_by_cycles(example_h5_path):
    test_data = BatteryDataset.from_batdata_hdf(example_h5_path)
    cycle_iter = iterate_cycles_from_file(example_h5_path, chunksize=4)  # Small to make sure we split cycles across chunks
    for streamed, (_, original) in zip_longest(cycle_iter, test_data.raw_data.groupby('cycle_number')):
        assert streamed is not None
        assert original is not None
        assert np.allclose(streamed['test_time'], original['test_time'])

    # Ensure we can generate chunks with metadata
    cycle_iter = iterate_cycles_from_file(example_h5_path, make_dataset=True)
    cycle_0 = next(cycle_iter)
    assert cycle_0.metadata == test_data.metadata
