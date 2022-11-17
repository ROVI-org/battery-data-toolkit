"""Methods that compute new data based on existing columns in a cycling data file"""

# TODO (wardlt): Create a base class for these operations to define an API

import logging

import numpy as np
from pandas import DataFrame
from scipy.signal import find_peaks

from batdata.schemas import ControlMethod

logger = logging.getLogger(__name__)


def add_method(df):
    """
    Tags the various charging, discharging, and rest methods
    that commonly occur in the raw data files

    Parameters
    ----------
    df : Pandas dataframe
        Battery testing data frame

    Examples
    --------
    none yet
    """
    # make a copy of input dataframe
    df['method'] = df['step_index']

    # array of indexes
    cycles = df.groupby(["cycle_number", "step_index"])
    logger.info('Identifying charging/discharging methods')
    for key, cycle in cycles:

        # pull out columns of interest and turn into numpy array
        # NOTE: (can be streamlined in future?)
        t = cycle["test_time"].values
        V = cycle["voltage"].values
        current = cycle['current'].values
        ind = cycle.index.values
        state = cycle['state'].values

        if len(ind) < 5 and state[0] == 0:
            # if there's a very short rest (less than 5 points)
            # we label as "anomalous rest"

            # df.at[ind, 'method'] = ControlMethod.short_rest
            df.loc[ind, 'method'] = ControlMethod.short_rest
        elif state[0] == 0:
            # if there are 5 or more points it's a
            # standard "rest"

            # df.at[ind, 'method'] = ControlMethod.rest
            df.loc[ind, 'method'] = ControlMethod.rest
        elif len(ind) < 5:
            # if it's a charge or discharage and there
            # are fewer than 5 points it is an
            # "anomalous charge or discharge"

            # df.at[ind, 'method'] = ControlMethod.short_nonrest
            df.loc[ind, 'method'] = ControlMethod.short_nonrest
        elif t[-1] - t[0] < 30:
            # if the step is less than 30 seconds
            # index as "pulse"

            # df.at[ind, 'method'] = ControlMethod.pulse
            df.loc[ind, 'method'] = ControlMethod.pulse
        else:
            # otherwise it is CC, CV or in-between

            # normalize voltage and current for purposes
            # of determining CC vs CV
            Vrng = max(V) - min(V)
            if Vrng == 0:
                df.loc[ind, 'method'] = ControlMethod.constant_voltage
                continue
            else:
                V = (max(V) - V) / Vrng

            max_abs_I = max(abs(current))
            if max_abs_I == 0:
                df.loc[ind, 'method'] = ControlMethod.rest 
            else:
                current = current / max_abs_I

            # get "differentials"
            dV = np.diff(V, prepend=0)
            dI = np.diff(current, prepend=0)
            dt = np.diff(t, prepend=0)

            dV[dV == 0] = np.nan
            dI[dI == 0] = np.nan
            dt[dt == 0] = np.nan

            a = dI / dt
            b = dV / dt
            a = abs(a / max(abs(a)))
            b = abs(b / max(abs(b)))
            a = a ** 2
            b = b ** 2
            # d = np.minimum(a, b)

            d = np.exp(abs(a - b)) - 1
            peaks, _ = find_peaks(d, distance=5, prominence=10 ** -3)

            extrema = [0] + list(peaks) + [len(d)]

            ind_tmp = np.array([None] * len(d))
            for i in range(len(extrema) - 1):
                low = extrema[i]
                high = extrema[i + 1]
                r = range(low, high)

                sI = abs(np.std(current[r]))
                sV = abs(np.std(V[r]))

                # Measure the ratio between the change and current and the change in the voltage
                if sI == 0 or sV == 0:
                    val = np.nan
                else:
                    val = sI / (sI + sV)

                if len(r) < 5 or t[high - 1] - t[low] < 10:
                    ind_tmp[r] = ControlMethod.other

                if val > 0.66:  # If the change in the current is 2x as large as the change in current
                    ind_tmp[r] = ControlMethod.constant_voltage
                elif val < 0.33:  # If voltage is 2x larger than the voltage
                    ind_tmp[r] = ControlMethod.constant_current
                else:  # Indeterminate
                    ind_tmp[r] = ControlMethod.other

            df.loc[ind, 'method'] = ind_tmp


def add_steps(df):
    """Compute the "step" index, which changes each time the state changes

    Parameters
    ----------
    df : Pandas dataframe
        Battery cycling data

    Examples
    --------
    none yet

    """

    logger.debug('Adding step indices')
    _determine_steps(df, 'state', 'step_index')


def add_substeps(df):
    """Compute the substep, which occurs when the control method changes

    Parameters
    ----------
    df: Pandas Dataframe
        Battery cycling data
    """
    logger.debug('Adding substep indices')
    _determine_steps(df, 'method', 'substep_index')


def _determine_steps(df: DataFrame, column: str, output_col: str):
    """Assign step indices based on whether there is a change in the value of a certain column

    Also resets the

    Parameters
    ----------
    df: pd.DataFrame
        Battery data
    column: str
        Column which to monitor for changes
    output_col: str
        Name in column which to store output results
    """
    #  A new step occurs when the previous step had a different value, so we compare against
    #   the array shifted forward one index
    change = df[column].ne(df[column].shift(periods=1, fill_value=df[column].iloc[0]))

    # The step number is equal to the number of changes observed previously in a batch
    #  Step 1: Compute the changes since the beginning of file
    df[output_col] = change.cumsum()

    # Step 2: Adjust so that each cycle starts with step 0
    for _, cycle in df.groupby("cycle_number"):
        df.loc[cycle.index, output_col] -= cycle[output_col].min()
