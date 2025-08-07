"""Tests that cover adding derived columns to the raw data"""
import numpy as np
import pandas as pd
from pytest import fixture
import pytest

from battdat.data import BatteryDataset
from battdat.postprocess.tagging import AddSteps, AddMethod, AddSubSteps, AddState
from battdat.schemas.column import ChargingState, ControlMethod


@fixture()
def synthetic_data() -> BatteryDataset:
    """Data which includes all of our types of steps"""

    # Make the segments
    rest_v = [3.5] * 16
    rest_i = [0.] * 16
    rest_s = [ChargingState.rest] * 16
    discharge_v = np.linspace(3.5, 3.25, 16)
    discharge_i = [-0.125] * 16
    discharge_s = [ChargingState.discharging] * 16
    shortrest_v = [3.25] * 4
    shortrest_i = [0] * 4
    shortrest_s = [ChargingState.rest] * 4
    shortnon_v = [3.25] * 4
    shortnon_i = [-0.1] * 4
    shortnon_s = [ChargingState.discharging] * 4
    pulse_v = [3.25] * 8
    pulse_i = [0.05] * 8
    pulse_s = [ChargingState.charging] * 8
    charge_v = [3.6] * 8 + np.linspace(3.6, 3.8, 8).tolist()
    charge_i = np.linspace(0.15, 0.1, 8).tolist() + [0.125] * 8
    charge_s = [ChargingState.charging] * 16

    # Combine them
    v = np.concatenate([rest_v, discharge_v, shortrest_v, shortnon_v, pulse_v, shortrest_v, charge_v])
    i = np.concatenate([rest_i, discharge_i, shortrest_i, shortnon_i, pulse_i, shortrest_i, charge_i])
    s = sum([rest_s, discharge_s, shortrest_s, shortnon_s, pulse_s, shortrest_s, charge_s], [])
    t = np.arange(len(v)) * 2.  # Assume measurements every 2 seconds
    c = np.zeros_like(t, dtype=int)  # All in the same cycle

    data = pd.DataFrame({
        'current': i,
        'voltage': v,
        'state': s,
        'test_time': t,
        'cycle_number': c
    })
    # data.drop([62, 63, 64], inplace=True)
    return BatteryDataset.make_cell_dataset(raw_data=data)


def test_example_data(synthetic_data):
    synthetic_data.validate_columns()


def test_step_detection(synthetic_data):
    AddSteps().enhance(synthetic_data.raw_data)

    # Should detect steps
    assert (synthetic_data.raw_data['step_index'].iloc[:16] == 0).all()
    assert (synthetic_data.raw_data['step_index'].iloc[16:32] == 1).all()
    assert (synthetic_data.raw_data['step_index'].iloc[32:36] == 2).all()
    assert (synthetic_data.raw_data['step_index'].iloc[36:40] == 3).all()
    assert (synthetic_data.raw_data['step_index'].iloc[40:48] == 4).all()
    assert (synthetic_data.raw_data['step_index'].iloc[48:52] == 5).all()
    assert (synthetic_data.raw_data['step_index'].iloc[52:68] == 6).all()


@pytest.mark.xfail
def test_method_detection(synthetic_data):
    # Start assuming that the step detection worked
    AddSteps().enhance(synthetic_data.raw_data)

    # See if we can detect the steps
    AddMethod().enhance(synthetic_data.raw_data)
    assert (synthetic_data.raw_data['method'].iloc[:16] == ControlMethod.rest).all()
    assert (synthetic_data.raw_data['method'].iloc[16:32] == ControlMethod.constant_current).all()
    assert (synthetic_data.raw_data['method'].iloc[32:36] == ControlMethod.short_rest).all()
    assert (synthetic_data.raw_data['method'].iloc[36:40] == ControlMethod.short_nonrest).all()
    assert (synthetic_data.raw_data['method'].iloc[40:48] == ControlMethod.pulse).all()
    assert (synthetic_data.raw_data['method'].iloc[48:52] == ControlMethod.short_rest).all()
    assert (synthetic_data.raw_data['method'].iloc[52:60] == ControlMethod.constant_voltage).all()
    assert (synthetic_data.raw_data['method'].iloc[60:68] == ControlMethod.constant_current).all()


@pytest.mark.xfail
def test_substep_detect(synthetic_data):
    # Start assuming that the step and method detection worked
    AddSteps().enhance(synthetic_data.raw_data)
    AddMethod().enhance(synthetic_data.raw_data)

    # The substeps should be the same as the steps because we do not have two charging/rest cycles next to each other
    AddSubSteps().enhance(synthetic_data.raw_data)
    assert (synthetic_data.raw_data['step_index'].iloc[:60] == synthetic_data.raw_data['substep_index'].iloc[:60]).all()
    assert (synthetic_data.raw_data['substep_index'].iloc[60:] == 7).all()


def test_state_detection(synthetic_data):
    # First, get only the data without the pre-defined state
    raw_data = synthetic_data.raw_data.drop(columns=['state'])

    # Enhance
    AddState().enhance(data=raw_data)

    # assert False, len(synthetic_data.raw_data)
    assert (raw_data['state'].iloc[:16] == ChargingState.rest).all(), raw_data['state'].iloc[:16]
    assert (raw_data['state'].iloc[16:32] == ChargingState.discharging).all(), raw_data['state'].iloc[16:32].to_numpy()
    assert (raw_data['state'].iloc[32:36] == ChargingState.rest).all()
    assert (raw_data['state'].iloc[36:40] == ChargingState.discharging).all()
    assert (raw_data['state'].iloc[40:48] == ChargingState.charging).all()
    assert (raw_data['state'].iloc[48:52] == ChargingState.rest).all()
    assert (raw_data['state'].iloc[52:] == ChargingState.charging).all()
