"""Base class and utilities related to post-processing on battery data"""
from typing import List

import pandas as pd

from batdata.data import BatteryDataset


class BaseFeatureComputer:
    """Base class for methods that produce new features given battery data

    Features can be anything but are often collected statistics about a certain cycle.
    """

    def compute_features(self, data: BatteryDataset) -> pd.DataFrame:
        """Compute

        Parameters
        ----------
        data: BatteryDataFrame
            Battery data object

        Returns
        -------
        features: pd.DataFrame
            A dataframe of features where rows are different cycles or steps, columns are different features
        """
        pass


class RawDataEnhancer(BaseFeatureComputer):
    """Base class for methods derives new data from the existing columns in raw data"""

    column_names: List[str] = ...

    def compute_features(self, data: BatteryDataset) -> pd.DataFrame:
        self.enhance(data.raw_data)
        return data.raw_data[self.column_names]

    def enhance(self, data: pd.DataFrame):
        """Add additional columns to the raw data

        Parameters
        ----------
        data: pd.DataFrame
            Raw data to be modified
        """
        ...
