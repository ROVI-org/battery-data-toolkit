"""Regression tests for non-mutating sign checks (issue #149)."""

import numpy as np
import pandas as pd
import pytest

from battdat.consistency.current import SignConventionChecker
from battdat.data import BatteryDataset


@pytest.fixture
def example_dataset():
    times = np.linspace(0, 1800, 256)
    current = np.zeros_like(times)
    current[128:] = 1.0
    voltage = np.ones_like(times)
    voltage[128:] = np.linspace(1.0, 1.3, 128)
    return BatteryDataset.make_cell_dataset(
        raw_data=pd.DataFrame({
            "test_time": times,
            "current": current,
            "voltage": voltage,
        })
    )


def test_sign_check_preserves_raw_data_and_hdf_export(example_dataset, tmp_path):
    original = example_dataset.raw_data.copy(deep=True)
    assert example_dataset.validate() == []
    example_dataset.to_hdf(tmp_path / "before.h5")

    assert SignConventionChecker().check(example_dataset) == []

    pd.testing.assert_frame_equal(example_dataset.raw_data, original)
    assert example_dataset.validate() == []
    example_dataset.to_hdf(tmp_path / "after.h5")


def test_sign_check_preserves_raw_data_when_warning_raised(example_dataset):
    example_dataset.raw_data["current"] *= -1
    original = example_dataset.raw_data.copy(deep=True)

    assert len(SignConventionChecker().check(example_dataset)) == 1
    pd.testing.assert_frame_equal(example_dataset.raw_data, original)
