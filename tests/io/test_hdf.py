from pathlib import Path

from pytest import raises, mark
import numpy as np
import pandas as pd
import tables

from battdat.data import BatteryDataset
from battdat.io.hdf import make_numpy_dtype_from_pandas, write_df_to_table, read_df_from_table, HDF5Writer, HDF5Reader
from battdat.schemas.column import ColumnSchema

example_df = pd.DataFrame({'a': [1, 2], 'b': [1., 3.], 'c': ['charge', 'discharge'], 'array': [[[1.]], [[0.]]]})


def test_dtype():
    dtype = make_numpy_dtype_from_pandas(example_df)
    assert dtype.names == ('a', 'b', 'c', 'array')
    assert dtype['array'].shape == (1, 1)


def test_store_df(tmpdir):
    with tables.open_file(tmpdir / "example.h5", "w") as file:
        group = file.create_group('/', name='base')
        table = write_df_to_table(file, group, 'table', example_df)
        assert tuple(table[0]) == (1, 1., b'charge', np.ones((1, 1)))

    with tables.open_file(tmpdir / "example.h5", "r") as file:
        table = file.get_node('/base/table')
        df_copy = read_df_from_table(table)
        assert (df_copy.columns == ['a', 'b', 'c', 'array']).all()
        assert np.allclose(df_copy['b'], [1., 3.])


def test_read_with_other_tables(tmpdir):
    writer = HDF5Writer()
    out_file = Path(tmpdir) / 'example.h5'

    # Write the same table through the writer (which puts metadata) and through the basic function (which does not)
    with tables.open_file(out_file, mode='w') as file:
        dataset = BatteryDataset(tables={'example_table': example_df},
                                 schemas={'example_table': ColumnSchema()})
        writer.write_to_hdf(dataset, file, None)
        write_df_to_table(file, file.root, 'extra_table', example_df)

    # Reading should only yield one table
    with tables.open_file(out_file) as file:
        dataset = HDF5Reader().read_from_hdf(file, None)
        assert set(dataset.tables.keys()) == {'example_table'}

    # Ensure error is raised if the schema is corrupted
    with tables.open_file(out_file, mode='a') as file:
        table = file.root['example_table']
        for corrupted in ("asdf", '{"a": 1}'):
            table._v_attrs['metadata'] = corrupted
            with raises(ValueError, match='marked as a battdat dataset but schema fails to read'):
                HDF5Reader().read_from_hdf(file, None)


@mark.parametrize('prefix', [None, 'a'])
def test_append(tmpdir, prefix):
    writer = HDF5Writer()
    out_file = Path(tmpdir) / 'example.h5'

    # Write the initial data
    with tables.open_file(out_file, mode='w') as file:
        if prefix is not None:
            file.create_group(file.root, prefix)

        writer.add_table(file, 'example_table', example_df, ColumnSchema(), prefix)

    # Append the data again
    with tables.open_file(out_file, mode='a') as file:
        writer.append_to_table(file, 'example_table', example_df, prefix)

        table = file.get_node('/example_table' if prefix is None else f'/{prefix}/example_table')
        df_copy = read_df_from_table(table)
        assert len(df_copy) == len(example_df) * 2
        assert np.allclose(df_copy['a'], [1, 2, 1, 2])
        assert np.equal(df_copy['c'], [b'charge', b'discharge'] * 2).all()

        # Test data check
        with raises(ValueError, match='Existing and new'):
            writer.append_to_table(file, 'example_table', pd.DataFrame({'a': [1., 2.]}), prefix)

        # Test bad prefix
        with raises(ValueError, match='No data available for prefix'):
            writer.append_to_table(file, 'example_table', pd.DataFrame({'a': [1., 2.]}), prefix='b')


def test_df_missing_strings(tmpdir):
    df = pd.DataFrame({'a': [None, 'a', 'bb']})
    with tables.open_file(tmpdir / "example.h5", "w") as file:
        group = file.create_group('/', name='base')
        table = write_df_to_table(file, group, 'table', df)
        assert tuple(table[-1]) == (b'bb',)
