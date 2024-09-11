from datetime import datetime

import requests
from pytest import fixture
from pydantic import AnyUrl

from batdata.extractors.batterydata import BDExtractor, generate_metadata


@fixture()
def test_files(file_path):
    return file_path / 'batterydata'


def test_detect_then_convert(test_files):
    # Find two files
    extractor = BDExtractor(store_all=False)
    group = next(extractor.identify_files(test_files))
    assert len(group) == 2

    # Parse them
    data = extractor.parse_to_dataframe(group)
    assert data.metadata.name == 'p492-13'

    # Test a few of columns which require conversion
    assert data.raw_data['cycle_number'].max() == 8
    first_measurement = datetime.fromtimestamp(data.raw_data['time'].iloc[0])
    assert first_measurement.year == 2020
    assert first_measurement.day == 3

    # Ensure it validates
    data.validate()


def test_store_all(test_files):
    """Make sure we get exactly one copy of all columns"""

    # Find two files
    extractor = BDExtractor(store_all=True)
    group = next(extractor.identify_files(test_files))
    data = extractor.parse_to_dataframe(group)

    # Make sure we only have the renamed `cycle_number` and not original `Cycle_Index`
    for df in [data.raw_data, data.cycle_stats]:
        assert 'cycle_number' in df.columns
        assert 'Cycle_Index' not in df.columns

    # Make sure NREL-specific columns are stored
    assert 'datenum_d' in data.cycle_stats.columns
    assert 'Charge_Throughput_Ah' in data.raw_data.columns


def test_metadata():
    source = 'kokam-nmc-gr-75ah-accelerated-aging'  # TODO (wardlt): Spoof a dataset if this changes
    description = requests.get(f'https://batterydata.energy.gov/api/3/action/package_show?id={source}', timeout=15).json()
    metadata = generate_metadata(description, ('https://test.url/',))
    assert AnyUrl('https://test.url/') in metadata.associated_ids
    assert metadata.battery.cathode.name == 'NMC111'
