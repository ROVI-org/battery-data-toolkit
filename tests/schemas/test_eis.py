from pytest import fixture, raises
import pandas as pd
import numpy as np

from batdata.schemas.eis import EISData


@fixture()
def example_df() -> pd.DataFrame:
    output = pd.DataFrame({
        'test_id': [1, 1],
        'frequency': [5e5, 4e5],
        'z_real': [0.241, 0.237],
        'z_imag': [0.431, 0.327],
    })
    output['z_mag'] = np.linalg.norm(output.values[:, -2:], axis=1)
    output['z_phase'] = np.rad2deg(np.arcsin(output['z_imag'] / output['z_mag']))
    return output


def test_pass(example_df):
    EISData().validate_dataframe(example_df)


def test_consistency(example_df):
    example_df['z_imag'] *= 2
    with raises(ValueError) as e:
        EISData().validate_dataframe(example_df)
    assert 'imag' in str(e.value)

    example_df['z_real'] *= 2
    with raises(ValueError) as e:
        EISData().validate_dataframe(example_df)
    assert 'real' in str(e.value)
