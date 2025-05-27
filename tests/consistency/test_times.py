"""Test for inconsistencies in time columns"""
from datetime import datetime

import numpy as np
import pandas as pd
from pytest import fixture

from battdat.consistency.time import TestTimeVsTimeChecker
from battdat.data import BatteryDataset


@fixture()
def example_dataset():
    df = pd.DataFrame({
        'voltage': [1.] * 8,
        'current': [0.] * 8,
        'test_time': np.arange(8, dtype=float)
    })
    df['time'] = datetime.now().timestamp() + df['test_time']
    data = BatteryDataset.make_cell_dataset(raw_data=df)
    data.validate()
    return data


def test_correct_inter(example_dataset):
    checker = TestTimeVsTimeChecker()
    assert len(checker.check(example_dataset)) == 0

    example_dataset.raw_data['time'].iloc[4:] += 0.2
    errors = checker.check(example_dataset)
    assert len(errors) == 1
    assert '2.0e-01 seconds' in errors[0]
    assert 'row 4. test_time=4 s' in errors[0]
