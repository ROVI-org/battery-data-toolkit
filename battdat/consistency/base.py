"""Base class for consistency checkers"""
from typing import List

from battdat.data import BatteryDataset


# TODO (wardlt): Consider standardizing the error messages: which table, how bad, possible remedy
# TODO (wardlt): Make attributes defining which subsets to explore part of the base class
class ConsistencyChecker:
    """Interface for classes which assess whether data in a :class:`~battdata.data.BatteryDataset` are self-consistent"""

    def check(self, dataset: BatteryDataset) -> List[str]:
        """Report possible inconsistencies within a dataset

        Args:
            dataset: Dataset to be evaluated
        Returns:
            List of observed inconsistencies
        """
        raise NotImplementedError()
