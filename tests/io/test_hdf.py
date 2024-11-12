import numpy as np
import pandas as pd
import tables

from battdat.io.hdf import make_numpy_dtype_from_pandas, write_df_to_table, read_df_from_table

example_df = pd.DataFrame({'a': [1, 2], 'b': [1., 3.], 'c': ['charge', 'discharge']})


def test_dtype():
    dtype = make_numpy_dtype_from_pandas(example_df)
    assert dtype.names == ('a', 'b', 'c')


def test_store_df(tmpdir):
    with tables.open_file(tmpdir / "example.h5", "w") as file:
        group = file.create_group('/', name='base')
        table = write_df_to_table(file, group, 'table', example_df)
        assert tuple(table[0]) == (1, 1., b'charge')

        df_copy = read_df_from_table(table)
        assert (df_copy.columns == ['a', 'b', 'c']).all()
        assert np.allclose(df_copy['b'], [1., 3.])
