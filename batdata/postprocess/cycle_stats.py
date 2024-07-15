"""Utility functions for computing properties of certain cycles"""
import warnings

import numpy as np
import pandas as pd

from batdata.postprocess.base import CycleSummarizer


class CycleTimes(CycleSummarizer):
    """Capture the start time and duration of a cycle

    The start of a cycle is the minimum test time for any point in the raw data.

    The duration of a cycle is the difference between the start of the next cycle and the start of the cycle.
    If the start time of the next cycle is unavailable, it is the difference between the test time of the
    last test time in the raw data and the start fo the cycle.
    """

    column_names = ['cycle_start', 'cycle_duration']

    def _summarize(self, raw_data: pd.DataFrame, cycle_data: pd.DataFrame):
        # Compute the starts and durations
        time_summary = raw_data.groupby('cycle_number')['test_time'].agg(
            cycle_start="min", cycle_duration=lambda x: max(x) - min(x), count=len
        ).reset_index()  # reset_index makes `cycle_number` a regular column
        if time_summary['count'].min() == 1:
            warnings.warn('Some cycles have only one measurements.')

        # Compute the duration using the start of the next cycle, if known
        time_summary['next_diff'] = time_summary['cycle_number'].diff(-1).iloc[:-1]
        if (time_summary['next_diff'].iloc[:-1] != -1).any():
            warnings.warn('Some cycles are missing from the dataframe. Time durations for those cycles may be too short')
        has_next_cycle = time_summary.query('next_diff == -1')
        time_summary.loc[has_next_cycle.index, 'cycle_duration'] = -time_summary['cycle_start'].diff(-1)[has_next_cycle.index]

        # Update the cycle_data accordingly
        cycle_data[self.column_names] = np.nan
        cycle_data.update(time_summary)
