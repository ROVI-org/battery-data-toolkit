"""Check for problems across the columns which describe time"""
from dataclasses import dataclass
from datetime import datetime
from typing import List

import numpy as np

from .base import ConsistencyChecker
from ..data import BatteryDataset


@dataclass
class TestTimeVsTimeChecker(ConsistencyChecker):
    """Ensure that the test time and timestamp columns agree

    Verify that the difference between the first and current row
    for the ``test_time`` (time elapsed since the beginning of cycling)
    and ``time`` (clock datetime) columns agree.
    """

    max_inconsistency: float = 0.1
    """Maximum inconsistency between timestamp and test time (s)"""

    def check(self, dataset: BatteryDataset) -> List[str]:
        output = []
        for name, subset in dataset.tables.items():
            if 'time' not in subset.columns or 'test_time' not in subset.columns:
                continue

            # Ensure that
            test_time_normed = subset['test_time'] - subset['test_time'].min()
            timestamp_normed = subset['time'] - subset['time'].min()
            diffs = np.abs(test_time_normed - timestamp_normed)
            max_diff = diffs.max()
            if max_diff > self.max_inconsistency:
                idx_max = np.argmax(diffs)
                date_max = datetime.fromtimestamp(subset['time'].iloc[idx_max])
                time_max = subset['test_time'].iloc[idx_max]
                output.append(f'Test times and timestep in dataset "{name}" differ by {max_diff:.1e} seconds in row {idx_max}.'
                              f' test_time={int(time_max)} s, time={date_max}')

        return output
