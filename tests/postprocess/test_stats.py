"""Test for simple statistics"""
import pandas as pd
import numpy as np

from pytest import warns

from batdata.data import BatteryDataset
from batdata.postprocess.cycle_stats import CycleTimes


def test_times():
    raw_data = pd.DataFrame({
        'cycle_number': [0, 0, 1, 1, 2, 2],
        'test_time': [0, 0.99, 1, 1.99, 2., 2.99]
    })
    data = BatteryDataset(raw_data=raw_data)
    CycleTimes().compute_features(data)
    assert np.isclose(data.cycle_stats['cycle_start'], [0., 1., 2.]).all()
    assert np.isclose(data.cycle_stats['cycle_duration'], [1., 1., 0.99]).all()

    # Make sure it warns if the next cycle is unavailable
    raw_data = pd.DataFrame({
        'cycle_number': [0, 0, 1, 1, 3, 3],  # As if cycle 2 is missing
        'test_time': [0, 0.99, 1, 1.99, 2., 2.99]
    })
    data = BatteryDataset(raw_data=raw_data)
    with warns(UserWarning) as w:
        CycleTimes().compute_features(data)
    assert 'Some cycles are missing' in str(w[0])
    assert len(w) == 1

    assert np.isclose(data.cycle_stats['cycle_start'], [0., 1., 2.]).all()
    assert np.isclose(data.cycle_stats['cycle_duration'], [1., 0.99, 0.99]).all()
