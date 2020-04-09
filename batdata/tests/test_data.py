"""Tests for the Battery data frame"""
import json
import os

import h5py
from pandas import HDFStore
from pytest import fixture

from batdata.data import BatteryDataFrame


@fixture()
def test_df():
    return BatteryDataFrame(data={
        'current': [1, 0, -1],
        'voltage': [2, 2, 2]
    }, metadata={'name': 'Test data'})


def test_write_hdf(tmpdir, test_df):
    """Test whether the contents of the HDF5 file are reasonably understandable"""

    # Write the HDF file
    out_path = os.path.join(tmpdir, 'test.h5')
    test_df.to_batdata_hdf(out_path)

    # Investigate the contents
    with h5py.File(out_path) as f:
        assert 'metadata' in f.attrs
        assert json.loads(f.attrs['metadata'])['name'] == 'Test data'
        assert 'raw_data' in f

    # Test writing to an already-open HDFStore
    store = HDFStore(out_path, 'r+')
    test_df.to_batdata_hdf(store)


def test_read_hdf(tmpdir, test_df):
    # Write it
    out_path = os.path.join(tmpdir, 'test.h5')
    test_df.to_batdata_hdf(out_path)

    # Test reading only the metadata
    metadata = BatteryDataFrame.get_metadata_from_hdf5(out_path)
    assert metadata.name == 'Test data'

    # Read it
    data = BatteryDataFrame.from_batdata_hdf(out_path)
    assert data.metadata.name == 'Test data'

    # Test reading from an already-open file
    store = HDFStore(out_path, 'r')
    data = BatteryDataFrame.from_batdata_hdf(store)
    assert data.metadata.name == 'Test data'


def test_dict(test_df):
    # Test writing it
    d = test_df.to_batdata_dict()
    assert d['metadata']['name'] == 'Test data'
    assert 'data' in d

    # Test reading it
    data = BatteryDataFrame.from_batdata_dict(d)
    assert len(data) == 3
    assert data.metadata.name == 'Test data'
