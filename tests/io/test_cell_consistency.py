"""Run consistency checks for data corresponding to cells"""
from battdat.consistency.current import SignConventionChecker

from pytest import mark

from battdat.io.arbin import ArbinReader
from battdat.io.batterydata import BDReader
from battdat.io.hdf import HDF5Reader

checkers = [
    SignConventionChecker()
]


@mark.parametrize(
    'reader,example_data',
    [(ArbinReader(), ['arbin_example.csv']),
     (BDReader(), ['batterydata/p492-13-raw.csv']),
     (HDF5Reader(), 'example-data/single-resistor-complex-charge_from-discharged.hdf')]
)
def test_consistency(reader, example_data, file_path):
    dataset = reader.read_dataset(
        [file_path / p for p in example_data] if isinstance(example_data, list) else file_path / example_data
    )
    for checker in checkers:
        warnings = checker.check(dataset)
        assert len(warnings) == 0, warnings
