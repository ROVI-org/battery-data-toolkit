import os

import numpy as np
from pytest import fixture

from batdata.extractors.arbin import ArbinExtractor
from batdata.postprocess.cycle_stats import compute_energy_per_cycle


@fixture
def example_data():
    ex_file = os.path.join(os.path.dirname(__file__), '..', '..', 'extractors', 'tests', 'files', 'arbin_example.csv')
    return ArbinExtractor().parse_to_dataframe([ex_file])


def test_cycle_stats(example_data):
    cyc, eng, cap = compute_energy_per_cycle(example_data)
    assert np.isclose([0, 1], cyc).all()
    assert np.isclose([3.256, 3.262], eng, atol=1e-2).all()
    assert np.isclose([1.073, 1.074], cap, atol=1e-2).all()
