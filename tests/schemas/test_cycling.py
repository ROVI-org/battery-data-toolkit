from batdata.schemas.column import RawData, DataType, ColumnSchema, ColumnInfo

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


def test_json():
    """Make sure we can serialize and deserialize classes"""

    as_json = RawData().model_dump_json()

    # Test deserialize using Pydantic, which requires knowing the base class
    schema = RawData.model_validate_json(as_json)
    assert schema.state.type == DataType.STATE

    # Test reading using the "unknown base" version
    schema = ColumnSchema.from_json(as_json)
    assert schema.state.type == DataType.STATE


def test_required():
    """Catch dataframe missing required columns"""

    d = pd.DataFrame()
    with raises(ValueError) as exc:
        RawData().validate_dataframe(d)
    assert 'missing a required column' in str(exc)


def test_extra_cols(example_df):
    """Handle extra columns"""
    example_df['extra'] = [1, 1]

    # Passes with extra columns by default
    RawData().validate_dataframe(example_df)

    # Fails when desired
    with raises(ValueError) as exc:
        RawData().validate_dataframe(example_df, allow_extra_columns=False)
    assert 'extra columns' in str(exc)


def test_get_item():
    schema = RawData()
    schema.extra_columns['test'] = ColumnInfo(description='Test')
    assert schema['test'].description == 'Test'
    assert schema['test_time'].units == 's'
    with raises(KeyError, match='asdf'):
        schema['asdf']


@mark.parametrize(
    "col,values",
    [('temperature', [1, 2]), ('file_number', [0.1, 0.2]), ('state', [1, 2])]
)
def test_type_failures(example_df, col, values):
    """Columns with the wrong type"""
    example_df[col] = values
    with raises(ValueError, match=col):
        RawData().validate_dataframe(example_df)


def test_monotonic(example_df):
    """Columns that should be monotonic but are not"""
    example_df['cycle_number'] = [2, 1]
    with raises(ValueError) as exc:
        RawData().validate_dataframe(example_df)
    assert 'monotonic' in str(exc)

    example_df['cycle_number'] = [1, 1]
    RawData().validate_dataframe(example_df)
