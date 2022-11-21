"""Tests for the Battery data frame"""
import json
import os

import h5py
import pandas as pd
from pandas import HDFStore
from pytest import fixture, raises

from batdata.data import BatteryDataset


@fixture()
def test_df():
    return BatteryDataset(raw_data=pd.DataFrame({
        'test_time': [0, 1, 2.],
        'current': [1., 0., -1.],
        'voltage': [2., 2., 2.],
        'other': [1, 2, 3]
    }), metadata={'name': 'Test data'})


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
    with HDFStore(out_path, 'r+') as store:
        test_df.to_batdata_hdf(store)


def test_read_hdf(tmpdir, test_df):
    # Write it
    out_path = os.path.join(tmpdir, 'test.h5')
    test_df.to_batdata_hdf(out_path)

    # Test reading only the metadata
    metadata = BatteryDataset.get_metadata_from_hdf5(out_path)
    assert metadata.name == 'Test data'

    # Read it
    data = BatteryDataset.from_batdata_hdf(out_path)
    assert data.metadata.name == 'Test data'

    # Test reading from an already-open file
    with HDFStore(out_path, 'r') as store:
        data = BatteryDataset.from_batdata_hdf(store)
    assert data.metadata.name == 'Test data'

    # Test requesting an unknown type of field
    with raises(ValueError) as exc:
        BatteryDataset.from_batdata_hdf(out_path, subsets=('bad)_!~',))
    assert 'bad)_!~' in str(exc)

    # Test reading an absent field
    with raises(ValueError) as exc:
        BatteryDataset.from_batdata_hdf(out_path, subsets=('cycle_stats',))
    assert 'File does not contain' in str(exc)


def test_dict(test_df):
    # Test writing it
    d = test_df.to_batdata_dict()
    assert d['metadata']['name'] == 'Test data'
    assert 'raw_data' in d

    # Test reading it
    data = BatteryDataset.from_batdata_dict(d)
    assert len(data.raw_data) == 3
    assert data.metadata.name == 'Test data'


def test_validate(test_df):
    # Make sure the provided data passes
    warnings = test_df.validate()
    assert len(warnings) == 1
    assert 'other' in warnings[0]

    # Make sure we can define new columns
    test_df.metadata.raw_data_columns['other'] = 'A column I added for testing purposes'
    warnings = test_df.validate()
    assert len(warnings) == 0

