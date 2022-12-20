"""Base class and utilities related to post-processing on battery data"""
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
