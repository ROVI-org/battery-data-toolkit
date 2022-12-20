"""Extractor for .npy tIVT-format files"""
from typing import Union, List, Iterator, Tuple
from logging import getLogger

import numpy as np
import pandas as pd

from batdata.extractors.base import BatteryDataExtractor
from batdata.schemas.cycling import ChargingState
from batdata.utils import drop_cycles
from batdata.postprocess.tagging import add_steps, add_method, add_substeps
from batdata.postprocess.cycle_stats import compute_capacity_energy

from scipy.interpolate import interp1d
from scipy.optimize import differential_evolution

logger = getLogger(__name__)


class TIVTExtractor(BatteryDataExtractor):
    """Parser for reading from .npy tIVT files

    Expects the files to be in .npy format
    """

    def group(self, files: Union[str, List[str]], directories: List[str] = None,
              context: dict = None) -> Iterator[Tuple[str, ...]]:
        for file in files:
            if file.lower().endswith('.npy'):
                yield file

    def generate_dataframe(self, file: str, file_number: int = 0, start_cycle: int = 0,
                           start_time: float = 0) -> pd.DataFrame:
        # load .npy file
        raw = np.load(file)
        t = raw[:, 0] - raw[0, 0]
        current = raw[:, 1]
        voltage = raw[:, 2]
        temp = raw[:, 3]

        # create dataframe
        df_out = pd.DataFrame()
        df_out['test_time'] = t
        df_out['current'] = current
        df_out['voltage'] = voltage
        df_out['temperature'] = temp

        # calculate cycles
        spd = 3600*24
        f = interp1d(t, current, kind='linear', fill_value='extrapolate')

        def err(offset):
            day_sts = np.arange(0, t.max(), spd)[:-1] + offset
            return -1*np.sum(f(day_sts))

        res = differential_evolution(err, [(0, spd)])
        offset = res.x[0] + 0.25*spd
        day_sts = np.arange(offset, t.max(), spd)
        day_sts_indx = [np.argmin(np.abs(t - day_st)) for day_st in day_sts]
        if np.unique(day_sts_indx).size < day_sts.size:
            logger.warning('repeated index')
        day_sts_bool = np.zeros(t.shape)
        day_sts_bool[day_sts_indx] = 1
        df_out['cycle_number'] = np.cumsum(day_sts_bool).astype('int64')

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

        # Add capacity and energy calculations
        df_out = compute_capacity_energy(df_out)

        return df_out

    def implementors(self) -> List[str]:
        return ['Noah, Paulson <npaulson@anl.gov>']

    def version(self) -> str:
        return '0.0.1'
