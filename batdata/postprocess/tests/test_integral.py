import os
from math import isclose

import numpy as np
from pytest import fixture

from batdata.data import BatteryDataset
from batdata.extractors.arbin import ArbinExtractor
from batdata.postprocess.integral import CapacityPerCycle, StateOfCharge


@fixture
def example_data() -> BatteryDataset:
    ex_file = os.path.join(os.path.dirname(__file__), '..', '..', 'extractors', 'tests', 'files', 'arbin_example.csv')
    return ArbinExtractor().parse_to_dataframe([ex_file])


def test_cycle_stats(example_data):
    feat = CapacityPerCycle().compute_features(example_data)
    assert np.isclose([0, 1], feat['cycle_number']).all()
    assert np.isclose([3.256, 3.262], feat['discharge_energy'], atol=1e-2).all()
    assert np.isclose([1.073, 1.074], feat['discharge_capacity'], atol=1e-2).all()


def test_capacity(example_data):
    StateOfCharge().enhance(example_data.raw_data)
    assert isclose(example_data.raw_data['capacity'].max(), 1.075, abs_tol=1e-1)
    assert 'energy' in example_data.raw_data
