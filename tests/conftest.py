from pathlib import Path

from pytest import fixture

from batdata.data import BatteryDataset, BatteryMetadata
from batdata.postprocess.timing import CycleTimes


@fixture()
def file_path() -> Path:
    """Path to test-related files"""
    return Path(__file__).parent / 'files'


@fixture()
def example_data(file_path) -> BatteryDataset:
    """An example dataset which contains metadata and a few cycles of data"""

    # Load the simple cycling
    path = file_path / 'example-data' / 'single-resistor-constant-charge_from-discharged.hdf'
    data = BatteryDataset.from_batdata_hdf(path)

    # Compute basic cycling states
    for stats in [CycleTimes()]:
        stats.compute_features(data)

    # Give the cell a name, at least
    data.metadata = BatteryMetadata(name='test')
    return data
