import numpy as np
import pandas as pd
from pytest import fixture

from battdat.data import CellDataset
from battdat.consistency.current import SignConventionChecker


@fixture()
def example_dataset():
    # Make a rest period followed by a charge where the voltage increases
    times = np.linspace(0, 1800, 256)
    current = np.zeros_like(times)
    current[128:] = 1.

    voltage = np.ones_like(times)
    voltage[128:] = np.linspace(1., 1.3, 128)

    return CellDataset(
        raw_data=pd.DataFrame({
            'test_time': times,
            'current': current,
            'voltage': voltage
        })
    )


def test_sign_checker(example_dataset):
    chcker = SignConventionChecker()
    result = chcker.check(example_dataset)
    assert len(result) == 0

    # Make sure swapping the sign breaks things
    example_dataset.datasets['raw_data']['current'] *= -1
    result = chcker.check(example_dataset)
    assert len(result) == 1
