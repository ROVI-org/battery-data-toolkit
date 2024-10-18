"""Evaluate streaming reads from files"""
from pathlib import Path

from pytest import fixture

from batdata.extractors.batterydata import BDExtractor
from batdata.streaming import iterate_records_from_file


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
