"""Tests related to the MACCOR parser"""
from datetime import datetime
from pytest import fixture, raises

from battdat.io.maccor import MACCORReader


@fixture()
def test_file(file_path):
    return file_path / 'maccor_example.001'


@fixture()
def extractor():
    return MACCORReader()


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


def test_date_check(extractor, test_file):
    files = [test_file, test_file.with_suffix('.002')]
    data = extractor.read_dataset(files)
    data.validate()
    assert data.raw_data['file_number'].max() == 1

    with raises(ValueError, match='not in the correct order'):
        extractor.read_dataset(files[::-1])


def test_time_parser(extractor, test_file):
    # With date and time in the time column
    df = extractor.read_file(test_file)
    assert datetime.fromtimestamp(df['time'].iloc[0]).month == 3

    # With only the time in the time column
    df = extractor.read_file(test_file.with_suffix('.002'))
    assert datetime.fromtimestamp(df['time'].iloc[0]).month == 4

    # Ignoring datetime
    extractor.ignore_time = True
    df = extractor.read_file(test_file)
    assert 'time' not in df.columns
