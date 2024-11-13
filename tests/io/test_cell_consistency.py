"""Run consistency checks for data corresponding to cells"""
from battdat.consistency.current import SignConventionChecker

from pytest import mark

from battdat.data import CellDataset
from battdat.io.arbin import ArbinReader
from battdat.io.batterydata import BDReader
from battdat.io.maccor import MACCORReader

checkers = [
    SignConventionChecker()
]


@mark.parametrize(
    'reader,example_data',
    [(ArbinReader(), ['arbin_example.csv']),
     (BDReader(), ['batterydata/p492-13-raw.csv'])]
)
def test_consistency(reader, example_data, file_path):
    reader.output_class = CellDataset
    dataset = reader.read_dataset([file_path / p for p in example_data])

    for checker in checkers:
        warnings = checker.check(dataset)
        assert len(warnings) == 0, warnings
