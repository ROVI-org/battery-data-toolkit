"""Extractor for MACCOR"""
import re
import logging
import itertools
from dataclasses import dataclass
from datetime import datetime
from typing import Union, List, Iterator, Tuple, Sequence, Optional

import pandas as pd
import numpy as np

from battdat.data import BatteryDataset
from battdat.io.base import DatasetFileReader, CycleTestReader, PathLike
from battdat.schemas import BatteryMetadata
from battdat.schemas.column import ChargingState
from battdat.postprocess.tagging import AddMethod, AddSteps, AddSubSteps
from battdat.utils import drop_cycles

_test_date_re = re.compile(r'Date of Test:\s+(\d{2}/\d{2}/\d{4})')

logger = logging.getLogger(__name__)


def correct_time_offsets(raw_data: pd.DataFrame, desync_tol: float = 0.01) -> int:
    """Correct errors in the timestamp column that result
    from the day not being listed with timestamp.

    Day rollovers are detected by desynchronization between the test time
    and timestamps, which are corrected by moving the test_time forward
    to meet the date time.

    Will warn if the desynchronization is not a multiple of a day,
    an hour (daylight savings time), or a second (leap seconds).

    Args:
        raw_data: Raw data signal to be corrected
        desync_tol: Tolerance of desynchronization between time columns
    Returns:
        Number of day rollovers that were detected
    """

    test_time = raw_data['test_time'] - raw_data['test_time'].iloc[0]

    def _get_differences():
        timestamp_diff = raw_data['time'] - raw_data['time'].iloc[0]
        return timestamp_diff - test_time

    while np.abs(diffs := _get_differences()).max() > desync_tol:
        # Get the amount of offset detected
        first_bad_ix = np.argmax(np.abs(diffs) > desync_tol)
        offset = diffs[first_bad_ix].item()

        # Check if it's consistent with a date rollover, daylight savings time, or leap second
        if np.isclose(offset % 86400, 0, atol=1e-1) or \
                np.isclose(np.abs(offset), [3600, 1], atol=1e-1).any():
            pass  # Nothing of concern
        else:
            logger.warning(f'Detected an offset inconsistent with a day: {offset} s')

        # Correct the offset
        raw_data['time'].iloc[first_bad_ix:] -= offset


@dataclass
class MACCORReader(CycleTestReader, DatasetFileReader):
    """Parser for reading from MACCOR-format files

    Expects the files to be ASCII files with a .### extension.
    The :meth:`group` operation will consolidate files such that all with
    the same prefix (i.e., everything except the numerals in the extension)
    are treated as part of the same experiment.
    """

    def group(self, files: Union[str, List[str]], directories: List[str] = None,
              context: dict = None) -> Iterator[Tuple[str, ...]]:
        if isinstance(files, str):
            files = [files]

        # Get only the MACCOR-style names
        valid_names = filter(lambda x: x[-3:].isdigit(), files)

        # Split then sort based on the prefix
        split_filenames = sorted(name.rsplit(".", maxsplit=1) for name in valid_names)

        # Return groups
        for prefix, group in itertools.groupby(split_filenames, key=lambda x: x[0]):
            yield tuple('.'.join(x) for x in group)

    def read_dataset(self, group: Sequence[PathLike] = (), metadata: Optional[BatteryMetadata] = None) -> BatteryDataset:
        # Verify the cells are ordered by test date
        start_dates = []
        for file in group:
            with open(file, 'r') as fp:
                header = fp.readline()
                test_date = _test_date_re.findall(header)[0]
                start_dates.append(datetime.strptime(test_date, '%m/%d/%Y'))

        # Make sure they are in the correct order
        if not all(x >= y for x, y in zip(start_dates[1:], start_dates)):
            msg = "\n  ".join(f'- {x} {y.strftime("%m/%d/%Y")}' for x, y in zip(group, start_dates))
            raise ValueError(f'Files are not in the correct order by test date: {msg}\n')

        return super().read_dataset(group, metadata)

    def read_file(self, file: PathLike, file_number: int = 0, start_cycle: int = 0,
                  start_time: int = 0) -> pd.DataFrame:

        # Pull the test date from the first line of the file
        with open(file, 'r') as fp:
            header = fp.readline()
        test_date = _test_date_re.findall(header)[0]

        # Read in the ASCII file (I found this notation works)
        df = pd.read_csv(file, skiprows=1, engine='python', sep='\t', index_col=False, encoding="ISO-8859-1")
        df = df.rename(columns={'DateTime': 'test_time'})

        # create fresh dataframe
        df_out = pd.DataFrame()

        # fill in new dataframe
        df_out['cycle_number'] = df['Cyc#'] + start_cycle - df['Cyc#'].min()
        df_out['cycle_number'] = df_out['cycle_number'].astype('int64')
        df_out['file_number'] = file_number  # df_out['cycle_number']*0
        df_out['test_time'] = df['Test (Min)'] * 60 - df['Test (Min)'].iloc[0] * 60 + start_time
        df_out['state'] = df['State']
        df_out['current'] = df['Amps']
        df_out['current'] = np.where(df['State'] == 'D', -1 * df_out['current'], df_out['current'])

        # Parse the timestamps
        def _parse_time(time: str) -> float:
            if '/' in time:
                return datetime.strptime(time, '%m/%d/%Y %H:%M:%S').timestamp()
            else:
                return datetime.strptime(f'{test_date} {time}', '%m/%d/%Y %H:%M:%S').timestamp()

        df_out['time'] = df['DPt Time'].apply(_parse_time)

        correct_time_offsets(df_out)

        #   0 is rest, 1 is charge, -1 is discharge
        df_out.loc[df_out['state'] == 'R', 'state'] = ChargingState.hold
        df_out.loc[df_out['state'] == 'C', 'state'] = ChargingState.charging
        df_out.loc[df_out['state'] == 'D', 'state'] = ChargingState.discharging
        df_out.loc[df_out['state'].apply(lambda x: x not in {'R', 'C', 'D'}), 'state'] = ChargingState.unknown

        df_out['voltage'] = df['Volts']
        df_out = drop_cycles(df_out)
        AddSteps().enhance(df_out)
        AddMethod().enhance(df_out)
        AddSubSteps().enhance(df_out)
        return df_out
