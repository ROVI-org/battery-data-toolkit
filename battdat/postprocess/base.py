"""Base class and utilities related to post-processing on battery data"""
from typing import List

import pandas as pd

from battdat.data import BatteryDataset
from battdat.schemas.column import ColumnSchema


class BaseFeatureComputer:
    """Base class for methods that produce new features given battery data

    Features can be anything but are often collected statistics about a certain cycle.
    """

    def compute_features(self, data: BatteryDataset) -> pd.DataFrame:
        """Compute

        Args:
            data: Battery data object

        Returns:
            A dataframe of features where rows are different cycles or steps, columns are different features
        """
        raise NotImplementedError()


class RawDataEnhancer(BaseFeatureComputer):
    """Base class for methods derives new data from the existing columns in raw data"""

    column_names: List[str] = ...

    def compute_features(self, data: BatteryDataset) -> pd.DataFrame:
        self.enhance(data.tables['raw_data'])
        return data.tables['raw_data'][self.column_names]

    def enhance(self, data: pd.DataFrame):
        """Add additional columns to the raw data

        Args:
            data: Raw data to be modified
        """
        raise NotImplementedError()


class CycleSummarizer(BaseFeatureComputer):
    """Classes which produce a summary of certain cycles given the raw data from a cycle"""

    column_names: List[str] = ...

    def compute_features(self, data: BatteryDataset) -> pd.DataFrame:
        self.add_summaries(data)
        return data.tables['cycle_stats'][['cycle_number'] + self.column_names]

    def add_summaries(self, data: BatteryDataset):
        """Add cycle-level summaries to a battery dataset

        Args:
            data: Dataset to be modified
        """

        # Add a cycle summary if not already available
        if 'cycle_stats' not in data.tables:
            data.tables['cycle_stats'] = pd.DataFrame({
                'cycle_number': sorted(set(data.tables['raw_data']['cycle_number']))
            })
            data.schemas['cycle_stats'] = ColumnSchema()

        # Perform the update
        self._summarize(data.tables['raw_data'], data.tables['cycle_stats'])

    def _summarize(self, raw_data: pd.DataFrame, cycle_data: pd.DataFrame):
        """Add additional data to a cycle summary dataframe

        Args:
            raw_data: Raw data describing the initial cycles. Is not modified
            cycle_data: Cycle data frame to be updated
        """
        raise NotImplementedError()
