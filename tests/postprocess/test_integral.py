from pathlib import Path

from pytest import mark
import numpy as np

from batdata.data import BatteryDataset
from batdata.extractors.batterydata import BDExtractor
from batdata.postprocess.integral import CapacityPerCycle, StateOfCharge


def get_example_data(file_path: Path, from_charged: bool) -> BatteryDataset:
    ex_file = file_path / 'example-data' / f'single-resistor-constant-charge_from-{"" if from_charged else "dis"}charged.hdf'
    return BatteryDataset.from_batdata_hdf(ex_file)


@mark.parametrize('from_charged', [True, False])
def test_cycle_stats(file_path, from_charged):
    example_data = get_example_data(file_path, from_charged)
    feat = CapacityPerCycle().compute_features(example_data)
    assert np.isclose([0], feat['cycle_number']).all()

    # Capacity is the 1 A-hr
    assert np.isclose([1.0], feat['discharge_capacity'], rtol=1e-2).all()
    assert np.isclose([1.0], feat['charge_capacity'], rtol=1e-2).all()

    # Energy to charge is (2.1 V + 3.1 V) / 2 * 1 A * 3600 s = 9360 J
    # Energy produced during discharge is (1.9 V + 2.9 V) * 1 A * 3600 s = 8640 J
    assert np.isclose([9360. / 3600], feat['charge_energy'], rtol=1e-2).all()
    assert np.isclose([8640. / 3600], feat['discharge_energy'], rtol=1e-2).all()


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
    data = BDExtractor().parse_to_dataframe(list((file_path / 'batterydata').glob('p492*')))
    orig_data = data.cycle_stats[['discharge_capacity', 'charge_capacity', 'discharge_energy', 'charge_energy']].copy().iloc[cyc_id]

    # Recompute
    CapacityPerCycle().compute_features(data)
    new_data = data.cycle_stats[['discharge_capacity', 'charge_capacity', 'discharge_energy', 'charge_energy']].iloc[cyc_id]
    diff = np.abs(orig_data.values - new_data.values)
    agree = diff < 1e-3
    assert agree.all(), diff
