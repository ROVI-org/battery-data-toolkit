from collections import defaultdict
from typing import Union, List, Iterator, Tuple, Optional

import pandas as pd

from .base import BatteryDataExtractor
from ..data import CellDataset


class BatteryArchiveExtractor(BatteryDataExtractor):
    """Convert the CSV file(s) from BatteryArchive into HDF5 format"""

    def group(self, files: Union[str, List[str]], directories: List[str] = None,
              context: dict = None) -> Iterator[Tuple[str, ...]]:
        # Special case: If given a single file, wrap it as a list
        if isinstance(files, str):
            files = [files]

        # Filter-out non CSV files
        csvs = [x for x in files if x.lower().endswith('.csv')]

        # Pair files in the same directory that begin with the same prefix
        paired_files = defaultdict(list)
        for file in csvs:
            file_lower = file.lower()

            # if it is denoted with BA's "timeseries" or "cycle_data" postfix,
            #  get the prefix and wait until we find its mate
            if file_lower.endswith('cycle_data.csv') or file_lower.endswith('timeseries.csv'):
                prefix = file[:-14]
                paired_files[prefix].append(file)

            # otherwise, return the file alone
            else:
                yield file

        # Return the paired groups of files
        for pair in paired_files.values():
            yield tuple(pair)

    def parse_timeseries_to_dataframe(self, path: str) -> pd.DataFrame:
        """Parse the time series data from a BatteryArchive CSV file

        Parameters
        ----------
        path: str
            Path to the CSV file

        Returns
        -------
        ts_data: pd.DataFrame
            Time series in a format ready for HDF5 file
        """

        # Read in the ASCII file (I found this notation works)
        df = pd.read_csv(path)
        df = df.rename(columns={'Test_Time (s)': 'test_time', 'Cycle_Index': 'cycle_number',
                                'Date_Time': 'date_time', 'Current (A)': 'current',
                                'Voltage (V)': 'voltage', 'Cell_Temperature (C)': 'temperature'})

        # Change the datatypes for the cycle_number
        df['cycle_number'] = df['cycle_number'].astype(int)

        return df

    def parse_to_dataframe(self, group: List[str], metadata: Optional[dict]):
        # TODO (wardlt): Do _something_ with the cycle-level data
        if len(group) == 1:
            ts_path = group[0]
        else:
            ts_path = [x for x in group if 'timeseries' in x][0]

        ts_data = self.parse_timeseries_to_dataframe(ts_path)
        return CellDataset(raw_data=ts_data, metadata=metadata)
