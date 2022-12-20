"""Utility functions for computing properties of certain cycles"""
from scipy.integrate import cumtrapz
import pandas as pd
import numpy as np

# TODO (wardlt): Add back in features I removed to simplify the code as other functions:
#   - [ ] Dropping outliers
#   - [ ] Smoothing with Gaussian Process regression
from batdata.schemas.cycling import ChargingState
from batdata.postprocess.base import BaseFeatureComputer
from batdata.data import BatteryDataset


class CapacityPerCycle(BaseFeatureComputer):
    """Compute the capacity and energy per cycle

    Capacity is computed by integrating the discharge segments of the battery

    Output dataframe has 3 columns:
        - ``cycle_ind``: Index of the cycle
        - ``energy``: Energy per the cycle in W-hr
        - ``capacity``: Capacity of the cycle in A-hr
    """

    def compute_features(self, data: BatteryDataset) -> pd.DataFrame:
        # Initialize the output arrays
        energies = []
        capacities = []
        cycle_ind = []

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

            # Append to the list
            energies.append(ene)
            capacities.append(cap)
            cycle_ind.append(cyc)

        return pd.DataFrame({
            'cycle_ind': cycle_ind,
            'energy': energies,
            'capacity': capacities
        })


# TODO (wardlt): Move this elsewhere? Does not quite match the API for the BaseFeatureComputer
def compute_charging_curve(df: BatteryDataset | pd.DataFrame) -> pd.DataFrame:
    """Compute estimates for the battery capacity for each measurement
    of the charging or discharging sections of each cycle.

    The capacity/energy for each cycle are determined independently,
    and is assumed to start at zero at the beginning of the cycle.

    Parameters
    ----------
    data:
        Battery dataset with raw data available, or the raw dataframe itself.
        Must have test_time, voltage and current columns.
        Processing will add "capacity" and "energy" columns with units
        of A-hr and W-hr, respectively.

    Returns
    -------
    curves: pd.DataFrame
        Charge and discharge curves for each cycle in a single dataframe
    """

    if not isinstance(df, pd.DataFrame):
        data = df.raw_data
    else:
        data = df

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

    return data
