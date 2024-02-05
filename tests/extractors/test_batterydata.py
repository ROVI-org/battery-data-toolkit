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
