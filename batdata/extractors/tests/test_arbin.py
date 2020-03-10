"""Tests related to the Arbin parser"""

import os

from batdata.extractors.arbin import ArbinExtractor

test_file = os.path.join(os.path.dirname(__file__), 'files', '2018-04-12_batch8_CH38.csv')


def test_validation():
    """Make sure the parser generates valid outputs"""
    arbin = ArbinExtractor()
    data = arbin.parse_to_dataframe([test_file])
    data.validate_columns(allow_extra_columns=False)
