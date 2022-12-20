import os
from math import isclose

import numpy as np
from pytest import fixture

from batdata.extractors.arbin import ArbinExtractor
from batdata.postprocess.integral import CapacityPerCycle, compute_charging_curve


@fixture
def example_data():
    ex_file = os.path.join(os.path.dirname(__file__), '..', '..', 'extractors', 'tests', 'files', 'arbin_example.csv')
    return ArbinExtractor().parse_to_dataframe([ex_file])


def test_cycle_stats(example_data):
    feat = CapacityPerCycle().compute_features(example_data)
    assert np.isclose([0, 1], feat['cycle_ind']).all()
    assert np.isclose([3.256, 3.262], feat['energy'], atol=1e-2).all()
    assert np.isclose([1.073, 1.074], feat['capacity'], atol=1e-2).all()


def test_capacity(example_data):
    example_data = compute_charging_curve(example_data)
    assert isclose(example_data['capacity'].max(), 1.075, abs_tol=1e-1)
    assert 'energy' in example_data
