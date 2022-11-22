"""Tests that cover adding derived columns to the raw data"""
import numpy as np
import pandas as pd
from pytest import fixture

from batdata.data import BatteryDataset
from batdata.postprocess.tagging import add_steps, add_method, add_substeps
from batdata.schemas import ChargingState, ControlMethod


@fixture()
def synthetic_data() -> BatteryDataset:
    """Data which includes all of our types of steps"""

    # Make the segments
    rest_v = [3.5] * 16
    rest_i = [0.] * 16
    rest_s = [ChargingState.hold] * 16
    discharge_v = np.linspace(3.5, 3.25, 16)
    discharge_i = [0.125] * 16
    discharge_s = [ChargingState.discharging] * 16
    shortrest_v = [3.25] * 4
    shortrest_i = [0] * 4
    shortrest_s = [ChargingState.hold] * 4
    shortnon_v = [3.25] * 4
    shortnon_i = [0.1] * 4
    shortnon_s = [ChargingState.discharging] * 4
    pulse_v = [3.25] * 8
    pulse_i = [-0.05] * 8
    pulse_s = [ChargingState.charging] * 8
    charge_v = [3.6] * 8 + np.linspace(3.6, 3.8, 8).tolist()
    charge_i = np.linspace(-0.15, -0.1, 8).tolist() + [-0.125] * 8
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
    return BatteryDataset(raw_data=data)


def test_example_data(synthetic_data):
    synthetic_data.validate_columns()


def test_step_detection(synthetic_data):
    add_steps(synthetic_data.raw_data)

    # Should detect steps
    assert (synthetic_data.raw_data['step_index'].iloc[:16] == 0).all()
    assert (synthetic_data.raw_data['step_index'].iloc[16:32] == 1).all()
    assert (synthetic_data.raw_data['step_index'].iloc[32:36] == 2).all()
    assert (synthetic_data.raw_data['step_index'].iloc[36:40] == 3).all()
    assert (synthetic_data.raw_data['step_index'].iloc[40:48] == 4).all()
    assert (synthetic_data.raw_data['step_index'].iloc[48:52] == 5).all()
    assert (synthetic_data.raw_data['step_index'].iloc[52:68] == 6).all()


def test_method_detection(synthetic_data):
    # Start assuming that the step detection worked
    add_steps(synthetic_data.raw_data)

    # See if we can detect the steps
    add_method(synthetic_data.raw_data)
    assert (synthetic_data.raw_data['method'].iloc[:16] == ControlMethod.rest).all()
    assert (synthetic_data.raw_data['method'].iloc[16:32] == ControlMethod.constant_current).all()
    assert (synthetic_data.raw_data['method'].iloc[32:36] == ControlMethod.short_rest).all()
    assert (synthetic_data.raw_data['method'].iloc[36:40] == ControlMethod.short_nonrest).all()
    assert (synthetic_data.raw_data['method'].iloc[40:48] == ControlMethod.pulse).all()
    assert (synthetic_data.raw_data['method'].iloc[48:52] == ControlMethod.short_rest).all()
    assert (synthetic_data.raw_data['method'].iloc[52:60] == ControlMethod.constant_voltage).all()
    assert (synthetic_data.raw_data['method'].iloc[60:68] == ControlMethod.constant_current).all()


def test_substep_detect(synthetic_data):
    # Start assuming that the step and method detection worked
    add_steps(synthetic_data.raw_data)
    add_method(synthetic_data.raw_data)

    # The substeps should be the same as the steps because we do not have two charging/rest cycles next to each other
    add_substeps(synthetic_data.raw_data)
    assert (synthetic_data.raw_data['step_index'].iloc[:60] == synthetic_data.raw_data['substep_index'].iloc[:60]).all()
    assert (synthetic_data.raw_data['substep_index'].iloc[60:] == 7).all()
