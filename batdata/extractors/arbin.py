"""Extractor for Arbin-format files"""
from typing import Union, List, Iterator, Tuple

import numpy as np
import pandas as pd

from batdata.extractors.base import BatteryDataExtractor
from batdata.schemas import ChargingState
from batdata.utils import drop_cycles
from batdata.postprocess import add_steps, add_method, add_substeps


class ArbinExtractor(BatteryDataExtractor):
    """Parser for reading from Arbin-format files

    Expects the files to be in CSV format
    """

    def group(self, files: Union[str, List[str]], directories: List[str] = None,
              context: dict = None) -> Iterator[Tuple[str, ...]]:
        for file in files:
            if file.lower().endswith('.csv'):
                yield file

    def generate_dataframe(self, file: str, file_number: int = 0, start_cycle: int = 0,
                           start_time: float = 0) -> pd.DataFrame:
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

        # Read the file and rename the file
        df = pd.read_csv(file)
        df = df.rename(columns={'DateTime': 'test_time'})

        # create fresh dataframe
        df_out = pd.DataFrame()

        # Convert the column names
        df_out['cycle_number'] = df['Cycle_Index'] + start_cycle - df['Cycle_Index'].min()
        df_out['cycle_number'] = df_out['cycle_number'].astype('int64')
        df_out['file_number'] = file_number  # df_out['cycle_number']*0
        df_out['test_time'] = np.array(df['test_time'] - df['test_time'][0] + start_time, dtype=float)
        df_out['current'] = df['Current']
        df_out['temperature'] = df['Temperature']
        df_out['internal_resistance'] = df['Internal_Resistance']
        df_out['voltage'] = df['Voltage']

        # Drop the duplicate rows
        df_out = drop_cycles(df_out)

        # Determine whether the battery is charging or discharging:
        #   0 is rest, 1 is charge, -1 is discharge
        # TODO (wardlt): This function should move to post-processing
        def compute_state(x):
            if abs(x) < self.eps:
                return ChargingState.hold
            return ChargingState.charging if x > 0 else ChargingState.discharging
        df_out['state'] = df_out['current'].apply(compute_state)

        # Determine the method uses to control charging/discharging
        add_steps(df_out)
        add_method(df_out)
        add_substeps(df_out)
        return df_out

    def implementors(self) -> List[str]:
        return ['Kubal, Joesph <kubal@anl.gov>', 'Ward, Logan <lward@anl.gov>']

    def version(self) -> str:
        return '0.0.1'
