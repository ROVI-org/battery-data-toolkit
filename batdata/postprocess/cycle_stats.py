"""Utility functions for computing properties of certain cycles"""

from batdata.data import BatteryDataFrame
import numpy as np


# TODO (wardlt): Add back in features I removed to simplify the code as other functions:
#   - [ ] Dropping outliers
#   - [ ] Smoothing with Gaussian Process regression

def compute_energy_per_cycle(df: BatteryDataFrame):
    """
    Calculate the maximum energy and capacity on a per-cycle basis

    Parameters
    ----------
    df : BatteryDataFrame
        Input dataframe

    Returns
    -------
    cycle_ind : array
        array of cycle numbers
    energies : array
        array of maximum for each cycle. Units: W-hr
    capacities : array
        array of maximum for each cycle. Units: A-hr

    Examples
    --------
    none yet

    """

    # Initialize the output arrays
    energies = np.array([])
    capacities = np.array([])
    cycle_ind = np.array([])

    # Loop over each cycle
    for cyc, cycle_data in df.query("state=='discharging'").groupby('cycle_number'):
        # Calculate accumulated energy/capacity for each sub-segment
        ene = 0
        cap = 0
        for _, subseg in cycle_data.groupby('substep_index'):
            # Sort by test time, just in case
            subseg_sorted = subseg.sort_values('test_time')

            # Use current as always positive convention, opposite of what our standard uses
            t = subseg_sorted['test_time'].values
            i = -1 * subseg_sorted['current'].values
            v = subseg_sorted['voltage'].values

            # integrate for energy and capacity and convert to
            # Watt/hrs. and Amp/hrs. respectively
            ene += np.trapz(i * v, t) / 3600
            cap += np.trapz(i, t) / 3600

        # TODO (wardlt): This version of append re-allocates arrays, O(n). Consider using list.append instead,
        #  which uses linked lists O(1)
        energies = np.append(energies, ene)
        capacities = np.append(capacities, cap)
        cycle_ind = np.append(cycle_ind, cyc)

    return cycle_ind, energies, capacities
