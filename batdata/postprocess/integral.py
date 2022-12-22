"""Features related to integral quantities (e.g., energy, capacity)"""
from typing import List, Sequence

import numpy as np
import pandas as pd
from scipy.integrate import cumtrapz

from batdata.postprocess.base import RawDataEnhancer, CycleSummarizer
from batdata.schemas.cycling import ChargingState


class CapacityPerCycle(CycleSummarizer):
    """Compute the capacity and energy at each time point

    Capacity is computed by integrating the charge or discharge segments of the battery.

    Output dataframe has 3 columns:
        - ``cycle_ind``: Index of the cycle
        - ``energy``: Energy per the cycle in W-hr
        - ``capacity``: Capacity of the cycle in A-hr
    """

    def __init__(self, states: Sequence[ChargingState] = (ChargingState.charging, ChargingState.discharging)):
        self.states = states
        assert all(x in [ChargingState.charging, ChargingState.discharging] for x in self.states), 'Only charging and discharging states allowed'

    @property
    def column_names(self) -> List[str]:
        output = []
        for state in self.states:
            name = state[:-3] + 'e'
            output.extend([f'{name}_energy', f'{name}_capacity'])
        return output

    def _summarize(self, raw_data: pd.DataFrame, cycle_data: pd.DataFrame):

        # Loop over any charge states the user wants
        for state in self.states:
            # Initialize the output arrays
            cycle_data.set_index('cycle_number', drop=False)
            name = state[:-3] + 'e'
            cycle_data[f'{name}_energy'] = np.nan
            cycle_data[f'{name}_capacity'] = np.nan

            # Loop over each cycle
            for cyc, cycle_subset in raw_data[raw_data['state'] == state].groupby('cycle_number'):
                # Calculate accumulated energy/capacity for each sub-segment
                ene = 0
                cap = 0
                for _, subseg in cycle_subset.groupby('substep_index'):
                    # Sort by test time, just in case
                    subseg_sorted = subseg.sort_values('test_time')

                    # Extract the test time, current and voltage
                    t = subseg_sorted['test_time'].values
                    i = subseg_sorted['current'].values
                    v = subseg_sorted['voltage'].values

                    # integrate for energy and capacity and convert to
                    # Watt/hrs. and Amp/hrs. respectively
                    ene += np.trapz(i * v, t) / 3600
                    cap += np.trapz(i, t) / 3600

                cycle_data.loc[cyc, f'{name}_energy'] = ene
                cycle_data.loc[cyc, f'{name}_capacity'] = cap


class StateOfCharge(RawDataEnhancer):
    """Compute estimates for the battery capacity for each measurement
    of the charging or discharging sections of each cycle.

    The capacity/energy for each cycle are determined independently,
    and is assumed to start at zero at the beginning of the cycle.
    """

    column_names = ['capacity', 'energy']

    def enhance(self, data: pd.DataFrame):
        # Add columns for the capacity and energy
        data['capacity'] = 0
        data['energy'] = 0

        # Compute the capacity and energy for each cycle
        for cid, cycle in data.groupby('cycle_number'):

            initial_cap = 0
            initial_ene = 0

            # Compute in segments over each subset (avoid issues with rests)
            for _, subcycle in cycle.groupby('substep_index'):
                # Integrate over it

                sel = subcycle['state'] == ChargingState.discharging
                sel += subcycle['state'] == ChargingState.charging
                if sum(sel) == 0:
                    data.loc[subcycle.index, 'capacity'] = initial_cap
                    data.loc[subcycle.index, 'energy'] = initial_ene
                    continue

                cap = cumtrapz(subcycle['current'],
                               subcycle['test_time'],
                               initial=0) / 3600  # Computes capacity in A-hr
                ene = cumtrapz(subcycle['current'] * subcycle['voltage'],
                               subcycle['test_time'],
                               initial=0) / 3600  # Energy in A-hr

                cap += initial_cap
                ene += initial_ene

                data.loc[subcycle.index, 'capacity'] = cap
                data.loc[subcycle.index, 'energy'] = ene

                initial_cap = cap[-1]
                initial_ene = ene[-1]
