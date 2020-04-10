"""Utility functions for computing properties of certain cycles"""
from scipy.integrate import cumtrapz

from batdata.data import BatteryDataFrame
import pandas as pd
import numpy as np


# TODO (wardlt): Add back in features I removed to simplify the code as other functions:
#   - [ ] Dropping outliers
#   - [ ] Smoothing with Gaussian Process regression
from batdata.schemas import ChargingState


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


def compute_charging_curve(df: BatteryDataFrame, discharge: bool = True) -> pd.DataFrame:
    """Compute estimates for the battery capacity for each measurement
    of the charging or discharging sections of each cycle.

    The capacity for each cycle are determined independently,
    and is assumed to start at zero at the beginning of the cycle.

    Parameters
    ----------
    df: BatteryDataFrame
        Battery dataset. Must have test_time, voltage and current columns.
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
    df = pd.DataFrame(df[df['state'] == (ChargingState.discharging if discharge else ChargingState.charging)])

    # Add columns for the capacity and energy
    df['capacity'] = 0
    df['energy'] = 0

    # Compute the capacity and energy for each cycle
    for cid, cycle in df.groupby('cycle_number'):

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
            df.loc[subcycle.index, 'capacity'] = cap
            df.loc[subcycle.index, 'energy'] = eng

    return df
