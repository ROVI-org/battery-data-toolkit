from abc import ABCMeta, abstractmethod
from typing import Tuple, List, Optional, Union

import pandas as pd
from materials_io.base import BaseParser

from batdata.data import BatteryDataset
from batdata.schemas import BatteryMetadata


class BatteryDataExtractor(BaseParser, metaclass=ABCMeta):
    def __init__(self, eps: float = 1e-10):
        """
        Args:
             eps (float): Tolerance for the CC vs CV identification
        """
        self.eps = eps

    @abstractmethod
    def generate_dataframe(self, file: str, file_number: int = 0, start_cycle: int = 0,
                           start_time: int = 0) -> pd.DataFrame:
        """Generate a DataFrame containing the data in this file

        The dataframe will be in our standard format

        Parameters
        ----------
        file: str
            Path to the file
        file_number: int
            Number of file, in case the test is spread across multiple files
        start_cycle: int
            Index to use for the first cycle, in case test is spread across multiple files
        start_time: float
            Test time to use for the start of the test, in case test is spread across multiple files

        Returns
        -------
        df: pd.DataFrame
            Dataframe containing the battery data in a standard format
        """
        pass

    def parse(self, group: List[str], context: dict = None) -> dict:
        if context is None:
            context = {}
        df_out = self.parse_to_dataframe(group, context.get('metadata', None))
        return df_out.to_batdata_dict()

    def parse_to_dataframe(self, group: List[str],
                           metadata: Optional[Union[BatteryMetadata, dict]] = None) -> BatteryDataset:
        """Parse a set of  files into a Pandas dataframe

        Parameters
        ----------
        group: list of str
            List of files to parse as part of the same test. Ordered sequentially
        metadata: dict, optional
            Metadata for the battery, should adhere to the BatteryMetadata schema

        Returns
        -------
        pd.DataFrame
            DataFrame containing the information from all files
        """

        # Initialize counters for the cycle numbers, etc.. Used to determine offsets for the
        start_cycle = 0
        start_time = 0

        # Read the data for each file
        #  Keep track of the ending index and ending time
        output_dfs = []
        for file_number, file in enumerate(group):
            # Read the file
            df_out = self.generate_dataframe(file, file_number, start_cycle, start_time)
            output_dfs.append(df_out)

            # Increment the start cycle and time to determine starting point of next file
            start_cycle += df_out['cycle_number'].max() - df_out['cycle_number'].min() + 1
            start_time = df_out['test_time'].max()

        # Combine the data from all files
        df_out = pd.concat(output_dfs, ignore_index=True)

        # Attach the metadata and return the data
        return BatteryDataset(raw_data=df_out, metadata=metadata)
