from pathlib import Path
from datetime import datetime
import json

import pandas as pd

from battdat.exporters.ba import BatteryArchiveExporter
from battdat.schemas import BatteryMetadata, BatteryDescription
from battdat.schemas.battery import ElectrodeDescription


def test_export(example_data, tmpdir):
    # Add a datetime
    example_data.raw_data['time'] = example_data.raw_data['test_time'] + datetime(year=2024, month=7, day=1).timestamp()

    # Add some metadata to the file
    example_data.metadata = BatteryMetadata(
        battery=BatteryDescription(
            anode=ElectrodeDescription(name='graphite', supplier='big-one'),
            cathode=ElectrodeDescription(name='nmc')
        )
    )

    tmpdir = Path(tmpdir)
    tmpdir.mkdir(exist_ok=True)
    exporter = BatteryArchiveExporter()
    exporter.export(example_data, tmpdir)

    # Make sure the time series loaded correctly
    timeseries_path = tmpdir.joinpath('cycle-timeseries-0.csv')
    assert timeseries_path.is_file()
    timeseries = pd.read_csv(timeseries_path)
    assert 'v' in timeseries  # Make sure a conversion occurred correctly
    assert 'cell_id' in timeseries
    assert timeseries['date_time'].iloc[0] == '07/01/2024 00:00:00.000000'
    assert timeseries['cycle_index'].iloc[1] == 1

    # Check that metadata was written
    metadata = json.loads(tmpdir.joinpath('metadata.json').read_text())
    assert metadata['cathode'] == '{"name":"nmc"}'

    # Make sure the cycle statistics are written
    cycle_stats = pd.read_csv(tmpdir.joinpath('cycle-stats.csv'))
    assert cycle_stats['cycle_index'].iloc[0] == 1
