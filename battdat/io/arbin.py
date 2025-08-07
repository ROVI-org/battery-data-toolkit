"""Extractor for Arbin-format files"""
from typing import Union, List, Iterator, Tuple

import numpy as np
import pandas as pd

from battdat.io.base import CycleTestReader
from battdat.schemas.column import ChargingState
from battdat.utils import drop_cycles
from battdat.postprocess.tagging import AddMethod, AddSteps, AddSubSteps


class ArbinReader(CycleTestReader):
    """Parser for reading from Arbin-format files

    Expects the files to be in CSV format"""

    def group(self, files: Union[str, List[str]], directories: List[str] = None,
              context: dict = None) -> Iterator[Tuple[str, ...]]:
        for file in files:
            if file.lower().endswith('.csv'):
                yield file

    def read_file(self, file: str, file_number: int = 0, start_cycle: int = 0,
                  start_time: float = 0) -> pd.DataFrame:

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
        df_out['current'] = df['Current']  # TODO (wardlt): Check this!?
        df_out['temperature'] = df['Temperature']
        df_out['internal_resistance'] = df['Internal_Resistance']
        df_out['voltage'] = df['Voltage']

        # Drop the duplicate rows
        df_out = drop_cycles(df_out)

        # Determine whether the battery is charging or discharging:
        #   0 is rest, 1 is charge, -1 is discharge
        # TODO (wardlt): This function should move to post-processing
        def compute_state(x):
            if abs(x) < 1e-6:
                return ChargingState.rest
            return ChargingState.charging if x > 0 else ChargingState.discharging

        df_out['state'] = df_out['current'].apply(compute_state)

        # Determine the method uses to control charging/discharging
        AddSteps().enhance(df_out)
        AddMethod().enhance(df_out)
        AddSubSteps().enhance(df_out)
        return df_out
