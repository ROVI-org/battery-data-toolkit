"""Base class for a battery data import and export tools"""
from typing import List, Optional, Union, Iterator, Sequence
from pathlib import Path
import os

import pandas as pd

from battdat.data import CellDataset, BatteryDataset
from battdat.schemas import BatteryMetadata

PathLike = Union[str, Path]


class DatasetReader:
    """Base class for tools which read battery data as a :class:`~battdat.data.BatteryDataset`

    All readers must implement a function which receives battery metadata as input and produces
    a completed :class:`battdat.data.BatteryDataset` as an output.

    Subclasses provide additional suggested operations useful when working with data from
    common sources (e.g., file systems, web APIs)
    """

    def read_dataset(self, metadata: Optional[Union[BatteryMetadata, dict]] = None, **kwargs) -> BatteryDataset:
        """Parse a set of  files into a Pandas dataframe

        Args:
            metadata: Metadata for the battery
        Returns:
            Dataset holding all available information about the dataset
        """
        raise NotImplementedError()


class DatasetFileReader(DatasetReader):
    """Tool which reads datasets written to files

    Provide an :meth:`identify_files` to filter out files likely to be in this format,
    or :meth:`group` function to find related file if data are often split into multiple files.
    """

    def identify_files(self, path: PathLike, context: dict = None) -> Iterator[tuple[PathLike]]:
        """Identify all groups of files likely to be compatible with this reader

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

    def group(self,
              files: Union[PathLike, List[PathLike]],
              directories: List[PathLike] = None,
              context: dict = None) -> Iterator[tuple[PathLike, ...]]:
        """Identify a groups of files and directories that should be parsed together

        Will create groups using only the files and directories included as input.

        The files of files are *all* files that could be read by this extractor,
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


class CycleTestReader(DatasetFileReader):
    """Template class for reading the files output by battery cell cyclers

    Adds logic for reading cycling time series from a list of files.
    """

    def read_file(self,
                  file: str,
                  file_number: int = 0,
                  start_cycle: int = 0,
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

    def read_dataset(self, group: Sequence[PathLike] = (), metadata: Optional[BatteryMetadata] = None) -> CellDataset:
        """Parse a set of  files into a Pandas dataframe

        Args:
            group: List of files to parse as part of the same test. Ordered sequentially
            metadata: Metadata for the battery, should adhere to the BatteryMetadata schema

        Returns:
            DataFrame containing the information from all files
        """

        # Initialize counters for the cycle numbers, etc., Used to determine offsets for the files read
        start_cycle = 0
        start_time = 0

        # Read the data for each file
        #  Keep track of the ending index and ending time
        output_dfs = []
        for file_number, file in enumerate(group):
            # Read the file
            df_out = self.read_file(file, file_number, start_cycle, start_time)
            output_dfs.append(df_out)

            # Increment the start cycle and time to determine starting point of next file
            start_cycle += df_out['cycle_number'].max() - df_out['cycle_number'].min() + 1
            start_time = df_out['test_time'].max()

        # Combine the data from all files
        df_out = pd.concat(output_dfs, ignore_index=True)

        # Attach the metadata and return the data
        return CellDataset(raw_data=df_out, metadata=metadata)


class DatasetWriter:
    """Tool which exports data from a :class:`~battdat.data.BatteryDataset` to disk in a specific format"""

    def export(self, dataset: BatteryDataset, path: Path):
        """Write the dataset to disk in a specific path

        All files from the dataset must be placed in the provided directory

        Args:
            dataset: Dataset to be exported
            path: Output path
        """
        raise NotImplementedError()
