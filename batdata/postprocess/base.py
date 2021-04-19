"""Base class and utilities realted to post-processing on battery data"""
import pandas as pd

from batdata.data import BatteryDataFrame


class BaseFeatureComputer:
    """Base class for methods that produce new features given battery data

    Features are per-cycle quantities that describe the state of the battery during that cycle
    """

    def compute_features(self, data: BatteryDataFrame) -> pd.DataFrame:
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
