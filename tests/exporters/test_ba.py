from pathlib import Path
import json

import pandas as pd

from batdata.exporters.ba import BatteryArchiveExporter
from batdata.schemas import BatteryMetadata, BatteryDescription
from batdata.schemas.battery import ElectrodeDescription


def test_export(example_data):
    # Add some metadata to the file
    example_data.metadata = BatteryMetadata(
        battery=BatteryDescription(
            anode=ElectrodeDescription(name='graphite', supplier='big-one'),
            cathode=ElectrodeDescription(name='nmc')
        )
    )

    tmpdir = Path('test')
    tmpdir.mkdir(exist_ok=True)
    exporter = BatteryArchiveExporter()
    exporter.export(example_data, tmpdir)

    # Make sure the time series loaded correctly
    timeseries_path = tmpdir.joinpath('cycle-timeseries-0.csv')
    assert timeseries_path.is_file()
    timeseries = pd.read_csv(timeseries_path)
    assert 'v' in timeseries  # Make sure a conversion occurred correctly
    assert 'cell_id' in timeseries

    # Check that metadata was written
    metadata = json.loads(tmpdir.joinpath('metadata.json').read_text())
    assert metadata['cathode'] == '{"name":"nmc"}'
