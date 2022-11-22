"""Extractor for MACCOR (untested!!)"""
from typing import Union, List, Iterator, Tuple

import pandas as pd
import numpy as np

from batdata.extractors.base import BatteryDataExtractor
from batdata.schemas import ChargingState
from batdata.postprocess import add_steps, add_method, add_substeps
from batdata.utils import drop_cycles


class MACCORExtractor(BatteryDataExtractor):
    """Parser for reading from Arbin-format files

    Expects the files to be ASCII files with a .### extension
    """

    def group(self, files: Union[str, List[str]], directories: List[str] = None,
              context: dict = None) -> Iterator[Tuple[str, ...]]:
        for file in files:
            if file[-3:].isdigit():
                yield file

    def generate_dataframe(self, file: str, file_number: int = 0, start_cycle: int = 0,
                           start_time: int = 0) -> pd.DataFrame:
        """Generate a DataFrame containing the data in this file

        The dataframe will be in our standard format

        Parameters
        ----------
        file: str
            Path to the file
        file_number: int
            Number of file, in case the test is spread across multiple files
        start_cycle: int
            Index to use for the first cycle, in case test is spread across multiple files
        start_time: float
            Test time to use for the start of the test, in case test is spread across multiple files

        Returns
        -------
        df: pd.DataFrame
            Dataframe containing the battery data in a standard format
        end_cycle: int
            Index of the final cycle
        end_time: float
            Test time of the last measurement
        """

        # Read in the ASCII file (I found this notation works)
        df = pd.read_csv(file, skiprows=1, engine='python', sep='\t')
        df = df.rename(columns={'DateTime': 'test_time'})

        # create fresh dataframe
        df_out = pd.DataFrame()

        # fill in new dataframe
        df_out['cycle_number'] = df['Cyc#'] + start_cycle - df['Cyc#'].min()
        df_out['cycle_number'] = df_out['cycle_number'].astype('int64')
        df_out['file_number'] = file_number  # df_out['cycle_number']*0
        df_out['test_time'] = df['Test (Min)'] * 60 - df['Test (Min)'][0] * 60 + start_time
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
