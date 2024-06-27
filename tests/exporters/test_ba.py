from pathlib import Path

import pandas as pd

from batdata.exporters.ba import BatteryArchiveExporter


def test_export(example_data, tmpdir):
    tmpdir = Path(tmpdir)
    exporter = BatteryArchiveExporter()
    exporter.export(example_data, tmpdir)

    # Make sure the time series loaded correctly
    timeseries_path = tmpdir.joinpath('cycle-timeseries-0.csv')
    assert timeseries_path.is_file()
    timeseries = pd.read_csv(timeseries_path)
    assert 'v' in timeseries  # Make sure a conversion occured correctly
