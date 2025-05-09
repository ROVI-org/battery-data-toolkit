"""Tests for the Battery data frame"""
import json
import os

import pytest
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from pydantic import ValidationError
from pytest import fixture, raises
from tables import File

from battdat.schemas.column import ColumnInfo
from battdat.data import BatteryDataset
from battdat import __version__


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
    dataset = BatteryDataset.make_cell_dataset(raw_data=raw_data, cycle_stats=cycle_stats, metadata={'name': 'Test data'})

    # Add an extra column in the schema
    dataset.schemas['raw_data'].extra_columns['new'] = ColumnInfo(description='An example column')
    return dataset


def test_write_hdf(tmpdir, test_df):
    """Test whether the contents of the HDF5 file are reasonably understandable"""

    # Write the HDF file
    out_path = os.path.join(tmpdir, 'test.h5')
    test_df.to_hdf(out_path)

    # Investigate the contents
    with File(out_path) as f:
        attrs = f.root._v_attrs
        assert 'metadata' in attrs
        assert json.loads(attrs['metadata'])['name'] == 'Test data'
        assert 'raw_data' in f.root

        # Make sure we have a schema
        g = f.root['raw_data']
        attrs = g._v_attrs
        assert 'metadata' in attrs
        assert json.loads(attrs['metadata'])['test_time']['units'] == 's'

    # Test writing to an already-open file
    with File(out_path, 'w') as file:
        test_df.to_hdf(file)


def test_read_hdf(tmpdir, test_df):
    # Write it
    out_path = os.path.join(tmpdir, 'test.h5')
    test_df.to_hdf(out_path)

    # Test reading only the metadata
    metadata = BatteryDataset.get_metadata_from_hdf5(out_path)
    assert metadata.name == 'Test data'

    # Read it
    data = BatteryDataset.from_hdf(out_path)
    assert 'raw_data' in data
    assert 'test_time' in data['raw_data'].columns
    assert len(data) == 2
    assert len(list(data)) == 2
    assert data.metadata.name == 'Test data'
    assert data.get('raw_data') is not None
    assert data['cycle_stats'] is not None
    assert data.schemas['raw_data'].extra_columns['new'].description == 'An example column'

    # Test reading from an already-open file
    with File(out_path, 'r') as file:
        data = BatteryDataset.from_hdf(file)
    assert data.metadata.name == 'Test data'

    # Test requesting an unknown type of field
    with raises(ValueError) as exc:
        BatteryDataset.from_hdf(out_path, tables=('bad)_!~',))
    assert 'bad)_!~' in str(exc)

    # Test reading an absent field
    del test_df.tables['cycle_stats']
    test_df.to_hdf(out_path)
    with raises(ValueError) as exc:
        BatteryDataset.from_hdf(out_path, tables=('cycle_stats',))
    assert 'File does not contain' in str(exc)


def test_multi_cell_hdf5(tmpdir, test_df):
    out_path = os.path.join(tmpdir, 'test.h5')

    # Save the cell once, then multiply the current by 2
    test_df.to_hdf(out_path, 'a')
    test_df['raw_data']['current'] *= 2
    test_df.to_hdf(out_path, 'b', overwrite=False)

    # Make sure we can count two cells
    _, names, _ = BatteryDataset.inspect_hdf(out_path)
    assert names == {'a', 'b'}

    with File(out_path) as h:
        _, names, schemas = BatteryDataset.inspect_hdf(h)
        assert names == {'a', 'b'}

    # Check that there are schemas for the raw_data
    assert 'current' in schemas['raw_data']

    # Load both
    test_a = BatteryDataset.from_hdf(out_path, prefix='a')
    test_b = BatteryDataset.from_hdf(out_path, prefix='b')
    assert np.isclose(test_a['raw_data']['current'] * 2, test_b['raw_data']['current']).all()

    # Test reading by index
    test_0 = BatteryDataset.from_hdf(out_path, prefix=0)
    assert np.isclose(test_0['raw_data']['current'],
                      test_a['raw_data']['current']).all()

    # Iterate over all
    keys = dict(BatteryDataset.all_cells_from_hdf(out_path))
    assert len(keys)
    assert np.isclose(keys['a']['raw_data']['current'] * 2,
                      keys['b']['raw_data']['current']).all()


def test_missing_prefix_warning(tmpdir, test_df):
    out_path = os.path.join(tmpdir, 'test.h5')

    test_df.to_hdf(out_path, 'a', overwrite=False)

    # Error if prefix not found
    with pytest.raises(ValueError, match='No data available'):
        BatteryDataset.from_hdf(out_path, prefix='b')


def test_multicell_metadata_warning(tmpdir, test_df):
    out_path = os.path.join(tmpdir, 'test.h5')

    # Save the cell once, then alter metadata
    test_df.to_hdf(out_path, 'a', overwrite=False)
    test_df.metadata.name = 'Not test data'
    with pytest.warns(UserWarning, match='differs from new metadata'):
        test_df.to_hdf(out_path, 'b', overwrite=False)


def test_validate(test_df):
    # Make sure the provided data passes
    warnings = test_df.validate()
    assert len(warnings) == 1
    assert 'other' in warnings[0]

    # Make sure we can define new columns
    test_df.schemas['raw_data'].extra_columns['other'] = ColumnInfo(description='Test')
    warnings = test_df.validate()
    assert len(warnings) == 0


def test_parquet(test_df, tmpdir):
    write_dir = tmpdir / 'parquet-test'
    written = test_df.to_parquet(write_dir)
    assert len(written) == 2
    for file in written.values():
        metadata = pq.read_metadata(file).metadata
        assert b'battery_metadata' in metadata
        assert b'table_metadata' in metadata

    # Read it back in, ensure data are recovered
    read_df = BatteryDataset.from_parquet(write_dir)
    assert (read_df.cycle_stats['cycle_number'] == test_df.cycle_stats['cycle_number']).all()
    assert (read_df.raw_data['voltage'] == test_df.raw_data['voltage']).all()
    assert read_df.metadata == test_df.metadata
    assert read_df.schemas['raw_data'].extra_columns['new'].description == 'An example column'

    # Test reading subsets
    read_df = BatteryDataset.from_parquet(write_dir, subsets=('cycle_stats',))
    assert read_df.metadata is not None
    with raises(AttributeError, match='raw_data'):
        assert read_df.raw_data
    assert read_df.cycle_stats is not None

    with raises(ValueError) as e:
        BatteryDataset.from_parquet(tmpdir)
    assert 'No data available' in str(e)

    # Test reading only metadata
    metadata = BatteryDataset.inspect_parquet(write_dir)
    assert metadata == test_df.metadata
    BatteryDataset.inspect_parquet(write_dir / 'cycle_stats.parquet')
    with raises(ValueError) as e:
        BatteryDataset.inspect_parquet(tmpdir)
    assert 'No parquet files' in str(e)


def test_version_warnings(test_df):
    # Alter the version number, then copy using to/from dict
    test_df.metadata.version = 'super.old.version'
    with pytest.warns() as w:
        BatteryDataset.make_cell_dataset(metadata=test_df.metadata, warn_on_mismatch=True)
    assert len(w) == 1  # Only the warning about the versions
    assert 'supplied=super.old.version' in str(w.list[0].message)

    # Make a change that will violate the schema
    test_df.metadata.name = 1  # Name cannot be an int

    with pytest.warns() as w:
        recovered = BatteryDataset.make_cell_dataset(metadata=test_df.metadata, warn_on_mismatch=True)
    assert len(w) == 3  # Warning during save, warning about mismatch, warning that schema failed
    assert 'supplied=super.old.version' in str(w.list[1].message)
    assert 'failed to validate, probably' in str(w.list[2].message)
    assert recovered.metadata.version == __version__


def test_bad_metadata():
    """Ensure bad metadata causes an exception"""

    metadata = {'name': 1}
    with raises(ValidationError):
        BatteryDataset.make_cell_dataset(metadata=metadata)
