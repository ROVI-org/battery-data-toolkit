"""Utility functions for computing properties of certain cycles"""
from scipy.integrate import cumtrapz

from batdata.data import BatteryDataset
import pandas as pd
import numpy as np


# TODO (wardlt): Add back in features I removed to simplify the code as other functions:
#   - [ ] Dropping outliers
#   - [ ] Smoothing with Gaussian Process regression
from batdata.schemas import ChargingState


def compute_energy_per_cycle(data: BatteryDataset):
    """
    Calculate the maximum energy and capacity on a per-cycle basis

    Parameters
    ----------
    data : BatteryDataset
        Input battery dataset. Must have raw data defined

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
    for cyc, cycle_data in data.raw_data.query("state=='discharging'").groupby('cycle_number'):
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


def compute_charging_curve(data: BatteryDataset, discharge: bool = True) -> pd.DataFrame:
    """Compute estimates for the battery capacity for each measurement
    of the charging or discharging sections of each cycle.

    The capacity for each cycle are determined independently,
    and is assumed to start at zero at the beginning of the cycle.

    Parameters
    ----------
    data: BatteryDataset
        Battery dataset with raw data available. Must have test_time, voltage and current columns.
        Processing will add "capacity" and "energy" columns with units
        of A-hr and W-hr, respectively
    discharge: bool
        Whether to compute the discharge or charge curve

    Returns
    -------
    curves: pd.DataFrame
        Charge and discharge curves for each cycle in a single dataframe
    """

    # Get only the [dis]charging data
    data = data.raw_data
    data = pd.DataFrame(data[data['state'] == (ChargingState.discharging if discharge else ChargingState.charging)])

    # Add columns for the capacity and energy
    data['capacity'] = 0
    data['energy'] = 0

    # Compute the capacity and energy for each cycle
    for cid, cycle in data.groupby('cycle_number'):

        # Compute in segments over each subset (avoid issues with rests)
        for _, subcycle in cycle.groupby('substep_index'):
            # Integrate over it
            cap = cumtrapz(subcycle['current'], subcycle['test_time'], initial=0) / 3600  # Computes capacity in A-hr
            eng = cumtrapz(subcycle['current'] * subcycle['voltage'],
                           subcycle['test_time'], initial=0) / 3600  # Energy in A-hr

            # Multiply by -1 for the discharging segment
            if discharge:
                cap *= -1
                eng *= -1
            data.loc[subcycle.index, 'capacity'] = cap
            data.loc[subcycle.index, 'energy'] = eng

    return data
