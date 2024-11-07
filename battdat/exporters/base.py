"""Interface definitions"""
from pathlib import Path

from battdat.data import BatteryDataset


class DatasetExporter:
    """Tool which exports data from a :class:`~battdat.data.BatteryDataset` to disk in a specific format

    Implementing an Exporter
    ------------------------
    """

    def export(self, dataset: BatteryDataset, path: Path):
        """Write the dataset to disk in a specific path

        All files from the dataset must be placed in the provided directory

        Args:
            dataset: Dataset to be exported
            path: Output path
        """
        raise NotImplementedError()
