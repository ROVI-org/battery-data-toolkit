"""Tests related to the Arbin parser"""

from battdat.io.arbin import ArbinReader


def test_validation(file_path):
    """Make sure the parser generates valid outputs"""
    arbin = ArbinReader()
    test_file = file_path / 'arbin_example.csv'
    data = arbin.read_dataset([test_file])
    data.validate_columns(allow_extra_columns=False)
