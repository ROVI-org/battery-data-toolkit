from batdata.schemas.cycling import CyclingData

from pytest import raises, fixture, mark
import pandas as pd


@fixture()
def example_df() -> pd.DataFrame:
    return pd.DataFrame({
        'cycle_number': [1, 2],
        'test_time': [0, 0.1],
        'voltage': [0.1, 0.2],
        'current': [0.1, -0.1],
        'state': ['charging', 'hold']
    })


def test_required():
    """Catch dataframe missing required columns"""

    d = pd.DataFrame()
    with raises(ValueError) as exc:
        CyclingData.validate_dataframe(d)
    assert 'missing a required column' in str(exc)


def test_extra_cols(example_df):
    """Handle extra columns"""
    example_df['extra'] = [1, 1]

    # Passes with extra columns by default
    CyclingData.validate_dataframe(example_df)

    # Fails when desired
    with raises(ValueError) as exc:
        CyclingData.validate_dataframe(example_df, allow_extra_columns=False)
    assert 'extra columns' in str(exc)


@mark.parametrize(
    "col,values",
    [('temperature', [1, 2]), ('file_number', [0.1, 0.2]), ('state', [1, 2])]
)
def test_type_failures(example_df, col, values):
    """Columns with the wrong type"""
    example_df[col] = values
    with raises(ValueError) as exc:
        CyclingData.validate_dataframe(example_df)
    assert 'is a' in str(exc)


def test_monotonic(example_df):
    """Columns that should be monotonic but are not"""
    example_df['cycle_number'] = [2, 1]
    with raises(ValueError) as exc:
        CyclingData.validate_dataframe(example_df)
    assert 'monotonic' in str(exc)

    example_df['cycle_number'] = [1, 1]
    CyclingData.validate_dataframe(example_df)
