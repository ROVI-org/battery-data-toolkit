from datetime import datetime
from pytest import fixture

from batdata.extractors.batterydata import BDExtractor


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
    assert data.raw_data['cycle_index'].max() == 7
    first_measurement = datetime.fromtimestamp(data.raw_data['time'].iloc[0])
    assert first_measurement.year == 2020
    assert first_measurement.day == 3

    # Ensure it validates
    data.validate()

