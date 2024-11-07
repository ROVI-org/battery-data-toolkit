"""Base class for a battery data extractor"""
from typing import List, Optional, Union, Iterator
from pathlib import Path
import os

import pandas as pd

from battdat.data import BatteryDataset
from battdat.schemas import BatteryMetadata


class BatteryDataExtractor:
    """Base class for a data extractors

    Implementing an Extractor
    -------------------------

    The minimum is to define the `generate_dataframe` method, which produces
    a data-frame containing the time-series data with standardized column names.

    If the data format contains additional metadata or cycle-level features,
    override the :meth:`parse_to_dataframe` such that it adds such data
    after parsing the time-series results.

    Provide an :meth:`identify_files` or :meth:`group` function to find related files
    if data are often split into multiple files.
    """
    def __init__(self, eps: float = 1e-10):
        self.eps = eps  # TODO (wardlt): Move this from extractor to post-processing logic

    def identify_files(self, path: str, context: dict = None) -> Iterator[tuple[str]]:
        """Identify all groups of files likely to be compatible with this extractor

        Uses the :meth:`group` function to determine groups of files that should be parsed together.

        Args:
            path: Root of directory to group together
            context: Context about the files
        Yields:
            Groups of eligible files
        """

        # Walk through the directories
        for root, dirs, files in os.walk(path):
            # Generate the full paths
            dirs = [os.path.join(root, d) for d in dirs]
            files = [os.path.join(root, f) for f in files]

            # Get any groups from this directory
            for group in self.group(files, dirs, context):
                yield group

    def group(self, files: Union[str, List[str]], directories: List[str] = None,
              context: dict = None) -> Iterator[tuple[str, ...]]:
        """Identify a groups of files and directories that should be parsed together

        Will create groups using only the files and directories included as input.

        The files of files are _all_ files that could be read by this extractor,
        which may include many false positives.

        Args:
            files: List of files to consider grouping
            directories: Any directories to consider group as well
            context: Context about the files
        Yields:
            Groups of files
        """

        # Make sure file paths are strings or Path-like objects
        if isinstance(files, str):
            files = [files]
        files = [Path(p) for p in files]

        # Default: Every file is in its own group
        for f in files:
            yield f,

    def generate_dataframe(self, file: str, file_number: int = 0, start_cycle: int = 0,
                           start_time: int = 0) -> pd.DataFrame:
        """Generate a DataFrame containing the data in this file

        The dataframe will be in our standard format

        Args:
            file: Path to the file
            file_number: Number of file, in case the test is spread across multiple files
            start_cycle: Index to use for the first cycle, in case test is spread across multiple files
            start_time: Test time to use for the start of the test, in case test is spread across multiple files

        Returns:
            Dataframe containing the battery data in a standard format
        """
        raise NotImplementedError()

    def parse_to_dataframe(self, group: List[str], metadata: Optional[Union[BatteryMetadata, dict]] = None) -> BatteryDataset:
        """Parse a set of  files into a Pandas dataframe

        Args:
            group: List of files to parse as part of the same test. Ordered sequentially
            metadata: Metadata for the battery, should adhere to the BatteryMetadata schema

        Returns:
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
