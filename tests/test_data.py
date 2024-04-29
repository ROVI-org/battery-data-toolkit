"""Tests for the Battery data frame"""
import json
import os

import h5py
import numpy as np
import pandas as pd
from pandas import HDFStore
import pyarrow.parquet as pq
from pytest import fixture, raises

from batdata.data import BatteryDataset


@fixture()
def test_df():
    raw_data = pd.DataFrame({
        'test_time': [0, 1, 2.],
        'current': [1., 0., -1.],
        'voltage': [2., 2., 2.],
        'other': [1, 2, 3],
    })
    cycle_stats = pd.DataFrame({
        'cycle_number': [0],
    })
    return BatteryDataset(raw_data=raw_data, cycle_stats=cycle_stats, metadata={'name': 'Test data'})


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
    assert data.raw_data is not None
    assert data.cycle_stats is not None

    # Test reading from an already-open file
    with HDFStore(out_path, 'r') as store:
        data = BatteryDataset.from_batdata_hdf(store)
    assert data.metadata.name == 'Test data'

    # Test requesting an unknown type of field
    with raises(ValueError) as exc:
        BatteryDataset.from_batdata_hdf(out_path, subsets=('bad)_!~',))
    assert 'bad)_!~' in str(exc)

    # Test reading an absent field
    test_df.cycle_stats = None
    test_df.to_batdata_hdf(out_path)
    with raises(ValueError) as exc:
        BatteryDataset.from_batdata_hdf(out_path, subsets=('cycle_stats',))
    assert 'File does not contain' in str(exc)


def test_multi_cell_hdf5(tmpdir, test_df):
    out_path = os.path.join(tmpdir, 'test.h5')

    # Save the cell once, then multiply the current by 2
    test_df.to_batdata_hdf(out_path, 'a')
    test_df.raw_data['current'] *= 2
    test_df.to_batdata_hdf(out_path, 'b', append=True)

    # Make sure we can count two cells
    _, names = BatteryDataset.inspect_batdata_hdf(out_path)
    assert names == {'a', 'b'}

    # Load both
    test_a = BatteryDataset.from_batdata_hdf(out_path, prefix='a')
    test_b = BatteryDataset.from_batdata_hdf(out_path, prefix='b')
    assert np.isclose(test_a.raw_data['current'] * 2, test_b.raw_data['current']).all()


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


def test_parquet(test_df, tmpdir):
    write_dir = tmpdir / 'parquet-test'
    written = test_df.to_batdata_parquet(write_dir)
    assert len(written) == 2
    for file in written.values():
        metadata = pq.read_schema(file).metadata
        assert b'battery_metadata' in metadata

    # Read it back in, ensure data are recovered
    read_df = BatteryDataset.from_batdata_parquet(write_dir)
    assert (read_df.cycle_stats['cycle_number'] == test_df.cycle_stats['cycle_number']).all()
    assert (read_df.raw_data['voltage'] == test_df.raw_data['voltage']).all()
    assert read_df.metadata == test_df.metadata

    # Test reading subsets
    read_df = BatteryDataset.from_batdata_parquet(write_dir, subsets=('cycle_stats',))
    assert read_df.metadata is not None
    assert read_df.raw_data is None
    assert read_df.cycle_stats is not None

    with raises(ValueError) as e:
        BatteryDataset.from_batdata_parquet(tmpdir)
    assert 'No data available' in str(e)

    # Test reading only metadata
    metadata = BatteryDataset.get_metadata_from_parquet(write_dir)
    assert metadata == test_df.metadata
    BatteryDataset.get_metadata_from_parquet(write_dir / 'cycle_stats.parquet')
    with raises(ValueError) as e:
        BatteryDataset.get_metadata_from_parquet(tmpdir)
    assert 'No parquet files' in str(e)
