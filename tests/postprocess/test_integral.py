from pathlib import Path

import pandas as pd
from pytest import mark
import numpy as np

from battdat.data import CellDataset
from battdat.io.batterydata import BDReader
from battdat.postprocess.integral import CapacityPerCycle, StateOfCharge


def get_example_data(file_path: Path, from_charged: bool) -> CellDataset:
    ex_file = file_path / 'example-data' / f'single-resistor-constant-charge_from-{"" if from_charged else "dis"}charged.hdf'
    return CellDataset.from_hdf(ex_file)


def test_short_cycles():
    """Make sure cycles that are too short for capacity measurements do not cause errors"""

    example_data = CellDataset(
        raw_data=pd.DataFrame({'time': range(2), 'current': [1.] * 2, 'voltage': [2.] * 2, 'cycle_number': [0] * 2})
    )
    CapacityPerCycle().compute_features(example_data)
    assert np.isnan(example_data.cycle_stats['capacity_charge']).all()


@mark.parametrize('from_charged', [True, False])
def test_cycle_stats(file_path, from_charged):
    example_data = get_example_data(file_path, from_charged)
    feat = CapacityPerCycle().compute_features(example_data)
    assert np.isclose([0], feat['cycle_number']).all()

    # Capacity is the 1 A-hr
    assert np.isclose([1.0], feat['capacity_discharge'], rtol=1e-2).all()
    assert np.isclose([1.0], feat['capacity_charge'], rtol=1e-2).all()

    # Energy to charge is (2.1 V + 3.1 V) / 2 * 1 A * 3600 s = 9360 J
    # Energy produced during discharge is (1.9 V + 2.9 V) * 1 A * 3600 s = 8640 J
    assert np.isclose([9360. / 3600], feat['energy_charge'], rtol=1e-2).all()
    assert np.isclose([8640. / 3600], feat['energy_discharge'], rtol=1e-2).all()


@mark.parametrize('from_charged', [True, False])
def test_capacity(file_path, from_charged):
    example_data = get_example_data(file_path, from_charged)
    soc = StateOfCharge()
    soc.enhance(example_data.raw_data)

    assert all(c in example_data.raw_data for c in soc.column_names)
    assert not any(example_data.raw_data[c].isna().any() for c in soc.column_names)

    # First cell should be 0
    assert np.isclose(example_data.raw_data.drop_duplicates('cycle_number', keep='first')[soc.column_names], 0).all()

    # Last cell of the capacity should be zero for our test cases
    assert np.isclose(example_data.raw_data['cycle_capacity'].iloc[-1], 0., atol=1e-3)

    # The capacity for the first few steps should be I*t/3600s
    first_steps = example_data.raw_data.iloc[:3]
    current = first_steps['current'].iloc[0]
    assert np.isclose(first_steps['cycle_capacity'], current * first_steps['test_time'] / 3600).all()

    # The energy for the first few steps should be
    #  discharging = I * \int_0^t (2.9 - t/3600) = I * (2.9t - t^2/7200)
    #  charging = I * \int_0^t (2.1 + t/3600) = I * (2.1t + t^2/7200)
    if from_charged:
        answer = current * (2.9 * first_steps['test_time'] - first_steps['test_time'] ** 2 / 7200)
        assert (answer[1:] < 0).all()
    else:
        answer = current * (2.1 * first_steps['test_time'] + first_steps['test_time'] ** 2 / 7200)
        assert (answer[1:] > 0).all()
    assert np.isclose(first_steps['cycle_energy'], answer / 3600, rtol=1e-3).all()


def test_against_battery_data_gov(file_path):
    """See if our capacities are similar to those computed in BatteryData.Energy.Gov"""

    cyc_id = 8
    data = BDReader().read_dataset(list((file_path / 'batterydata').glob('p492*')))
    orig_data = \
        data.cycle_stats[
            ['capacity_discharge', 'capacity_charge', 'energy_discharge', 'energy_charge']
        ].copy().iloc[cyc_id]

    # Recompute
    CapacityPerCycle().compute_features(data)
    new_data = data.cycle_stats[['capacity_discharge', 'capacity_charge', 'energy_discharge', 'energy_charge']].iloc[
        cyc_id]
    diff = np.abs(orig_data.values - new_data.values)
    agree = diff < 1e-3
    assert agree.all(), diff


def test_reuse_integrals(file_path):
    example_data = get_example_data(file_path, True)

    # Get a baseline capacity
    CapacityPerCycle(reuse_integrals=False).compute_features(example_data)
    initial_data = example_data.cycle_stats[
        ['capacity_discharge', 'capacity_charge', 'energy_discharge', 'energy_charge']].copy()

    # Compute the integrals then intentionally increase capacity and energy 2x
    StateOfCharge().compute_features(example_data)
    for c in ['cycle_energy', 'cycle_capacity']:
        example_data.raw_data[c] *= 2

    # Recompute capacity and energy measurements, which should have increased by 2x
    CapacityPerCycle(reuse_integrals=True).compute_features(example_data)
    final_data = example_data.cycle_stats[
        ['capacity_discharge', 'capacity_charge', 'energy_discharge', 'energy_charge']].copy()
    assert np.isclose(initial_data.values * 2, final_data.values, atol=1e-3).all()
