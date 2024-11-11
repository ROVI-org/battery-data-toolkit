"""Tests related to the MACCOR parser"""
from pytest import fixture

from battdat.io.maccor import MACCORExtractor


@fixture()
def test_file(file_path):
    return file_path / 'maccor_example.001'


@fixture()
def extractor():
    return MACCORExtractor()


def test_validation(extractor, test_file):
    """Make sure the parser generates valid outputs"""
    data = extractor.read_dataset([test_file])
    data.validate_columns(allow_extra_columns=False)


def test_grouping(extractor, tmp_path):
    # Make a file structure with two sets of experiments and a nonsense file
    for f in ['README', 'testA.002', 'testA.001', 'testB.001']:
        (tmp_path / f).write_text('junk')

    # Test the grouping
    groups = list(extractor.identify_files(tmp_path))
    assert len(groups) == 2
    assert (str(tmp_path / 'testA.001'), str(tmp_path / 'testA.002')) in groups
    assert (str(tmp_path / 'testB.001'),) in groups
