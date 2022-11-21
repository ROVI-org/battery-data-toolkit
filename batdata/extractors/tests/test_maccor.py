"""Tests related to the MACCOR parser"""

import os
from batdata.extractors.maccor import MACCORExtractor

test_file = os.path.join(os.path.dirname(__file__), 'files', 'maccor_example.001')


def test_validation():
    """Make sure the parser generates valid outputs"""
    extractor = MACCORExtractor()
    data = extractor.parse_to_dataframe([test_file])
    data.validate_columns(allow_extra_columns=False)
