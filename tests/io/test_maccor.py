"""Tests related to the MACCOR parser"""
import numpy as np
import pandas as pd
from datetime import datetime
from pytest import fixture, raises

from battdat.consistency.time import TestTimeVsTimeChecker
from battdat.io.maccor import MACCORReader, correct_time_offsets


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


def test_check_offset_correct(caplog):
    df = pd.DataFrame({
        'test_time': np.arange(3, dtype=float),
    })

    # Test the OK offsets
    for off in [86400, 1, -3600]:
        df['time'] = df['test_time'] + datetime.now().timestamp()
        df['time'].iloc[1:] += off
        correct_time_offsets(df)
        assert np.allclose(df['time'] - df['time'].iloc[0], np.arange(3.))
        assert len(caplog.messages) == 0

    # Test an offset which yields a warning
    df['time'].iloc[1:] += 25
    correct_time_offsets(df)
    assert len(caplog.messages) == 1
    assert '25' in caplog.messages[-1]


def test_grouping(extractor, tmp_path):
    # Make a file structure with two sets of experiments and a nonsense file
    for f in ['README', 'testA.002', 'testA.001', 'testB.001']:
        (tmp_path / f).write_text('junk')

    # Test the grouping
    groups = list(extractor.identify_files(tmp_path))
    assert len(groups) == 2
    assert (str(tmp_path / 'testA.001'), str(tmp_path / 'testA.002')) in groups
    assert (str(tmp_path / 'testB.001'),) in groups


def test_test_time_multifile(extractor, test_file):
    """Ensure we get the time between starting files correctly"""
    files = [test_file, test_file.with_suffix('.002')]
    data = extractor.read_dataset(files)
    data.validate()

    assert len(TestTimeVsTimeChecker().check(data)) == 0  # That the test times and date columns are correct


def test_date_check(extractor, test_file):
    """Test detecting out-of-order files"""
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
    assert datetime.fromtimestamp(df['time'].iloc[0]).day == 1
    assert datetime.fromtimestamp(df['time'].iloc[-1]).day == 2
