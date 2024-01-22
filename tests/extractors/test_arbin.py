"""Tests related to the Arbin parser"""

from batdata.extractors.arbin import ArbinExtractor


def test_validation(file_path):
    """Make sure the parser generates valid outputs"""
    arbin = ArbinExtractor()
    test_file = file_path / 'arbin_example.csv'
    data = arbin.parse_to_dataframe([test_file])
    data.validate_columns(allow_extra_columns=False)
