"""Checks related to the current in time series data"""
from dataclasses import dataclass
from typing import List, Collection, Optional

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from battdat.data import BatteryDataset
from battdat.consistency.base import ConsistencyChecker


# TODO (wardlt): Check over different cycles
@dataclass
class SignConventionChecker(ConsistencyChecker):
    """Estimate whether the sign convention of a dataset is likely to be correct

    The concept underpinning this class is that the voltage of a cell should increase as it is charged.
    The algorithm looks for a period where the current is the most consistent the measures whether
    the change in measured voltage during that period.
    """

    subsets_to_check: Collection[str] = ('raw_data',)
    """Which subsets within a dataset to evaluate"""
    window_length: float = 360.
    """Length of time period over which to assess voltage change (units: s)"""
    minimum_current: float = 1e-6
    """Minimum current used when determining periods of charge or discharge"""

    def check(self, dataset: BatteryDataset) -> List[str]:
        warnings = []
        for subset in self.subsets_to_check:
            if (warning := self.check_subset(dataset.datasets[subset])) is not None:
                warnings.append(warning)
        return warnings

    def check_subset(self, time_series: pd.DataFrame) -> Optional[str]:
        # Convert the test time (seconds) to a time object so that Panda's rolling window can use a time
        time_series['timestamp'] = time_series['test_time'].apply(datetime.fromtimestamp)
        nonzero_current = time_series.query(f'current > {self.minimum_current} or current < {-self.minimum_current}')  # Only get nonzero currents
        windowed = nonzero_current[['timestamp', 'test_time', 'current', 'voltage']].rolling(
            window=timedelta(seconds=self.window_length), on='timestamp', min_periods=4,
        )
        if len(nonzero_current) < 4:
            raise ValueError(f'Insufficient data to judge the sign convention (only {len(nonzero_current)}). Consider raising the minimum current threshold.')

        # Find the region with the lowest standard deviation
        most_stable_point = windowed['current'].std().idxmin()
        most_stable_time = nonzero_current['test_time'].loc[most_stable_point]
        stable_window = nonzero_current.query(f'test_time < {most_stable_time} and test_time > {most_stable_time - self.window_length}')
        curr_volt_cov = np.cov(stable_window['voltage'], stable_window['test_time'])[0, 1]
        if np.sign(curr_volt_cov) != np.sign(stable_window['current'].mean()):
            return (f'Potential sign error in current. Average current between test_time={most_stable_time - self.window_length:.1f}s and '
                    f'test_time={most_stable_time:.1f} is {stable_window["current"].mean():.1e} A and the covariance between the voltage and current '
                    f'is {curr_volt_cov:.1e} V-s. The current and this covariance should have the same sign.')
