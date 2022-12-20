"""Extractor for MACCOR (untested!!)"""
import itertools
from typing import Union, List, Iterator, Tuple

import pandas as pd
import numpy as np

from batdata.extractors.base import BatteryDataExtractor
from batdata.schemas import ChargingState
from batdata.postprocess.tagging import add_method, add_steps, add_substeps
from batdata.utils import drop_cycles


class MACCORExtractor(BatteryDataExtractor):
    """Parser for reading from Arbin-format files

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

    def generate_dataframe(self, file: str, file_number: int = 0, start_cycle: int = 0,
                           start_time: int = 0) -> pd.DataFrame:

        # Read in the ASCII file (I found this notation works)
        df = pd.read_csv(file, skiprows=1, engine='python', sep='\t', index_col=False)
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
        #   0 is rest, 1 is charge, -1 is discharge
        df_out.loc[df_out['state'] == 'R', 'state'] = ChargingState.hold
        df_out.loc[df_out['state'] == 'C', 'state'] = ChargingState.charging
        df_out.loc[df_out['state'] == 'D', 'state'] = ChargingState.discharging
        df_out.loc[df_out['state'] == 'O', 'state'] = ChargingState.unknown
        df_out.loc[df_out['state'] == 'S', 'state'] = ChargingState.unknown

        df_out['voltage'] = df['Volts']
        df_out = drop_cycles(df_out)
        add_steps(df_out)
        add_method(df_out)
        add_substeps(df_out)

        return df_out

    def implementors(self) -> List[str]:
        return ['Kubal, Joesph <kubal@anl.gov>', 'Ward, Logan <lward@anl.gov>']

    def version(self) -> str:
        return '0.0.1'
