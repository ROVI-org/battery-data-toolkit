"""Methods which assign labels that are present in some testing machines yet absent in others.

For example, :meth:`add_method` determines whether the battery is being held at a constant voltage or current."""
import logging

import numpy as np
from pandas import DataFrame
from scipy.signal import find_peaks, savgol_filter

from batdata.schemas import ControlMethod, ChargingState

logger = logging.getLogger(__name__)


def add_method(df):
    """Adds the various charging, discharging, and rest methods
    that commonly occur in the raw data files.

    Determines whether a charging step is composed of constant-current, constant-voltage,
    or mixed steps by first partitioning it into substeps based on the maximum curvature
    of these points then assigning regions to constant voltage or current if one varied
    more than twice the other.

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
        t = cycle["test_time"].values
        voltage = cycle["voltage"].values
        current = cycle['current'].values
        ind = cycle.index.values
        state = cycle['state'].values

        if len(ind) < 5 and state[0] == ChargingState.hold:
            # if there's a very short rest (less than 5 points)
            # we label as "anomalous rest"
            df.loc[ind, 'method'] = ControlMethod.short_rest
        elif state[0] == ChargingState.hold:
            # if there are 5 or more points it's a
            # standard "rest"
            df.loc[ind, 'method'] = ControlMethod.rest
        elif len(ind) < 5:
            # if it's a charge or discharge and there
            # are fewer than 5 points it is an
            # "anomalous charge or discharge"
            df.loc[ind, 'method'] = ControlMethod.short_nonrest
        elif t[-1] - t[0] < 30:
            # if the step is less than 30 seconds
            # index as "pulse"
            df.loc[ind, 'method'] = ControlMethod.pulse
        else:
            # Normalize the voltage and current before determining which one moves "more"
            for x in [voltage, current]:
                x -= x.min()
                x /= max(x.max(), 1e-6)

            # First see if there are significant changes in the charging behavior
            #  We use a https://en.wikipedia.org/wiki/Savitzky%E2%80%93Golay_filter to get smooth
            #  derviatives, which requires even spacing.
            #  So, our first step will be to make sure that the spacings are relatively even
            dt = t[1:] - t[:-1]
            if dt.std() / dt.mean() > 1e-6:
                raise ValueError('We do not yet support non-even spacing.')

            d2v_dt2 = savgol_filter(voltage, 5, 4, deriv=2)
            d2i_dt2 = savgol_filter(current, 5, 4, deriv=2)
            current_peaks, _ = find_peaks(d2i_dt2, distance=5, prominence=10 ** -3)
            voltage_peaks, _ = find_peaks(d2v_dt2, distance=5, prominence=10 ** -3)

            # Assign a control method to the segment between each of these peaks

            extrema = [0] + list(set(current_peaks).union(set(voltage_peaks))) + [len(voltage)]

            methods = []
            for i in range(len(extrema) - 1):
                # Get the segment between these two peaks
                low = extrema[i]
                high = extrema[i + 1]
                r = np.arange(low, high).tolist()

                # Measure the ratio between the change and current and the change in the voltage
                s_i = current[r].std()
                s_v = voltage[r].std()
                val = s_i / (s_i + s_v)

                if val > 0.66:  # If the change in the current is 2x as large as the change in current
                    method = ControlMethod.constant_voltage
                elif val < 0.33:  # If voltage is 2x larger than the voltage
                    method = ControlMethod.constant_current
                else:
                    method = ControlMethod.other
                methods.extend([method] * len(r))

            df.loc[ind, 'method'] = methods


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
