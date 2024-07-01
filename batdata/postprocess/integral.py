"""Features related to integral quantities (e.g., energy, capacity)"""
import warnings
from itertools import zip_longest
from typing import List

import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid

from batdata.postprocess.base import RawDataEnhancer, CycleSummarizer


class CapacityPerCycle(CycleSummarizer):
    """Compute the observed capacity and energy during both charge and discharge of each cycle

    Determines capacities based on the integral of current over each cycle:

    1. Compute the change in state of charge from the start of the cycle
       by computing the integral of the capacity over time.
       We refer to this integral as the dSOC.
    2. Determine whether the battery started from a charged state
       by determining if the largest capacity change is positive
       (i.e., if the point most different state of charge from the
       start is _more discharged_ than the starting point).
       The code will raise a warning if the quantities are similar.
    3. If starting from a charged state, the discharge capacity
       is the maximum change in state of charge (``dSOC.max()``).
       The charge capacity is the amount of charge transferred to the
       battery between this maximally-discharged state and the end
       the of the cycle (``dSOC.max() - dSOC[-1]``)
    4. If starting from a discharged state, the charge capacity
       is the maximum change in state of charge and the discharge capacity
       is the amount transferred from the battery into the end of the cycle.

    The energy is computed using a similar procedure, but by integrating
    the product of current and voltage instead of only current.

    .. note::

        Measurements of capacity and energy assume a cycle returns
        the battery to the same state as it started the cycle.

    Output dataframe has 4 new columns.
        - ``capacity_discharge``: Discharge capacity per cycle in A-hr
        - ``capacity_charge``: Charge capacity per the cycle in A-hr
        - ``energy_charge``: Discharge energy per cycle in J
        - ``energy_discharge``: Charge energy per the cycle in J
    The full definitions are provided in the :class:`~batdata.schemas.cycling.CycleLevelData` schema
    """

    def __init__(self, reuse_integrals: bool = True):
        """

        Args:
            reuse_integrals: Whether to reuse the ``cycle_capacity`` and ``cycle_energy`` if they are available
        """
        self.reuse_integrals = reuse_integrals

    @property
    def column_names(self) -> List[str]:
        output = []
        for name in ['charge', 'discharge']:
            output.extend([f'energy_{name}', f'capacity_{name}'])
        return output

    def _summarize(self, raw_data: pd.DataFrame, cycle_data: pd.DataFrame):
        # Initialize the output arrays
        cycle_data.set_index('cycle_number', drop=False)
        for name in self.column_names:
            cycle_data[name] = np.nan

        # Get the indices of the beginning of each cycle
        raw_data = raw_data.reset_index()  # Ensure a sequential ordering from 0
        start_inds = raw_data.drop_duplicates('cycle_number', keep='first').index

        # Loop over each cycle. Using the starting point of this cycle and the first point of the next as end caps
        for cyc, (start_ind, stop_ind) in enumerate(zip_longest(start_inds, start_inds[1:] + 1, fillvalue=len(raw_data))):
            cycle_subset = raw_data.iloc[start_ind:stop_ind]

            # Perform the integration
            if self.reuse_integrals and 'cycle_energy' in cycle_subset.columns and 'cycle_capacity' in cycle_subset.columns:
                capacity_change = cycle_subset['cycle_capacity'].values * 3600  # To A-s
                energy_change = cycle_subset['cycle_energy'].values * 3600  # To J
            else:
                capacity_change = cumulative_trapezoid(cycle_subset['current'], x=cycle_subset['test_time'])
                energy_change = cumulative_trapezoid(cycle_subset['current'] * cycle_subset['voltage'], x=cycle_subset['test_time'])

            # Estimate if the battery starts as charged or discharged
            max_charge = capacity_change.max()
            max_discharge = -capacity_change.min()

            starts_charged = max_discharge > max_charge
            if np.isclose(max_discharge, max_charge, rtol=0.01):
                warnings.warn(f'Unable to clearly detect if battery started charged or discharged in cycle {cyc}. '
                              f'Amount discharged is {max_discharge:.2e} A-s, charged is {max_charge:.2e} A-s')

            # Assign the charge and discharge capacity
            #  One capacity is beginning to maximum change, the other is maximum change to end
            if starts_charged:
                discharge_cap = max_discharge
                charge_cap = capacity_change[-1] + max_discharge
                discharge_eng = -energy_change.min()
                charge_eng = energy_change[-1] + discharge_eng
            else:
                charge_cap = max_charge
                discharge_cap = max_charge - capacity_change[-1]
                charge_eng = energy_change.max()
                discharge_eng = charge_eng - energy_change[-1]

            cycle_data.loc[cyc, 'energy_charge'] = charge_eng / 3600.  # To W-hr
            cycle_data.loc[cyc, 'energy_discharge'] = discharge_eng / 3600.
            cycle_data.loc[cyc, 'capacity_charge'] = charge_cap / 3600.  # To A-hr
            cycle_data.loc[cyc, 'capacity_discharge'] = discharge_cap / 3600.


class StateOfCharge(RawDataEnhancer):
    """Compute the change in capacity and system energy over each cycle

    The capacity change for a cycle is determined by integrating the
    current as a function of time between the start of the cycle
    and the first of the next cycle.
    The energy change is determined by integrating the product
    of current and voltage.

    Output dataframe has 4 new columns:
        - ``cycle_capacity``: Amount of charge dispersed from the battery over the cycle, in A-hr
        - ``cycle_energy``: Amount of energy dispersed from the battery over the cycle, in J
    """

    column_names = ['cycle_capacity', 'cycle_energy']

    def enhance(self, data: pd.DataFrame):
        # Add columns for the capacity and energy
        for c in self.column_names:
            data[c] = np.nan

        # Compute the capacity and energy for each cycle
        ordered_copy = data.reset_index()  # Ensure a sequential ordering from 0
        start_inds = ordered_copy.drop_duplicates('cycle_number', keep='first').index

        # Loop over each cycle
        for cyc, (start_ind, stop_ind) in enumerate(zip_longest(start_inds, start_inds[1:] + 1, fillvalue=len(ordered_copy) + 1)):
            cycle_subset = ordered_copy.iloc[start_ind:stop_ind]

            # Perform the integration
            capacity_change = cumulative_trapezoid(cycle_subset['current'], x=cycle_subset['test_time'], initial=0)
            energy_change = cumulative_trapezoid(cycle_subset['current'] * cycle_subset['voltage'], x=cycle_subset['test_time'], initial=0)

            # Store them in the raw data
            data.loc[cycle_subset['index'], 'cycle_capacity'] = capacity_change / 3600  # To A-hr
            data.loc[cycle_subset['index'], 'cycle_energy'] = energy_change / 3600  # To W-hr
