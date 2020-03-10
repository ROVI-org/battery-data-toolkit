from typing import Tuple
from pandas import DataFrame
import logging

logger = logging.getLogger(__name__)


# TODO (wardlt): Move to post-processing?
def drop_cycles(df: DataFrame, digit: int = 2):
    """
    Drop duplicate cycles from a dataframe.

    Cycles must meet the following criteria
    that meet the following criteria:
    the Voltage and Current must be exactly the same,
    and the time between steps must be identical to 2 digits.
    They can sometimes vary by some epsilon for the Arbin data

    Parameters
    ----------
    df : Pandas DataFrame
        input dataframe
    digit : int
        number of digits to round to in time index (in seconds)
        
    Returns
    -------
    df : Pandas DataFrame
        dataframe without the duplicate columns


    Examples
    --------
    none yet

    """

    # NOTE: we have already converted time to seconds

    # add rounded time to dataframe
    df['TMP'] = df['test_time']
    logger.debug('Removing duplicates from dataframe')

    # round time to specified number of digits
    df = df.round({'TMP': digit})
    len1 = len(df)

    # drop points where the rounded time, voltage and current are identical
    # keep only first instance
    df.drop_duplicates(subset=['TMP', 'voltage', 'current'], keep='first', inplace=True)

    # re-index dataframe with points dropped
    df.reset_index(drop=True, inplace=True)

    # calculate number of cycles dropped
    dropped = len1 - len(df)
    logger.debug(f'Dropped {dropped} lines')

    # remove the now-unneed column
    df.drop(columns=['TMP'], inplace=True)
    
    return df
