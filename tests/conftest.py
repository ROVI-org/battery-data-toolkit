from pathlib import Path

from pytest import fixture

from battdat.data import BatteryMetadata, BatteryDataset
from battdat.postprocess.timing import CycleTimesSummarizer


@fixture()
def file_path() -> Path:
    """Path to test-related files"""
    return Path(__file__).parent / 'files'


@fixture()
def example_data(file_path) -> BatteryDataset:
    """An example dataset which contains metadata and a few cycles of data"""

    # Load the simple cycling
    path = file_path / 'example-data' / 'single-resistor-constant-charge_from-discharged.hdf'
    data = BatteryDataset.from_hdf(path)

    # Compute basic cycling states
    for stats in [CycleTimesSummarizer()]:
        stats.compute_features(data)

    # Give the cell a name, at least
    data.metadata = BatteryMetadata(name='test')
    return data
