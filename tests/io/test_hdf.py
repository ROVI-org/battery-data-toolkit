from pathlib import Path

from pytest import raises, mark
import numpy as np
import pandas as pd
import tables

from battdat.io.hdf import make_numpy_dtype_from_pandas, write_df_to_table, read_df_from_table, HDF5Writer
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

        df_copy = read_df_from_table(table)
        assert (df_copy.columns == ['a', 'b', 'c', 'array']).all()
        assert np.allclose(df_copy['b'], [1., 3.])


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

        # Test data check
        with raises(ValueError, match='Existing and new'):
            writer.append_to_table(file, 'example_table', pd.DataFrame({'a': [1., 2.]}), prefix)

        # Test bad prefix
        with raises(ValueError, match='No data available for prefix'):
            writer.append_to_table(file, 'example_table', pd.DataFrame({'a': [1., 2.]}), prefix='b')
