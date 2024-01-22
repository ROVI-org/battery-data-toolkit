from pathlib import Path

from pytest import fixture


@fixture()
def file_path() -> Path:
    """Path to test-related files"""
    return Path(__file__).parent / 'files'
