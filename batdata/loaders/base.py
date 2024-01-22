"""Base class for data loader"""
from typing import TypeVar, Generic, Iterator
from pathlib import Path

import pandas as pd
import numpy as np

from batdata.data import BatteryDataset

InputType = TypeVar('InputType')
"""Type of data used to represent the inputs to a machine learning model"""
OutputType = TypeVar('OutputType')
"""Type of data used to represent the outputs of a machine learning model"""


# TODO (wardlt): Refactor to make the operations performed by the loader separate objects so we can mix/match

class BaseBatteryLoader(Generic[InputType]):
    """Base class for battery data loaders

    Provides the functionality for generating inputs and outputs in the format
    required for our CNN model

    - *Input*: A 2D matrix of discharge capacity at fixed voltage intervals
               for each cycle being used in the training set
    - *Output*: The observed capacity fade starting at the first cycle
                after that used for the training set

    Args:
        cells: A list of cells or paths to battery data in HDF5 format
        batch_size: Number of batteries to use per batch
        random_seed: Random seed for generating batches
        required_data: Which data must be in the provided cells
    """

    required_data: list[str]
    """Fields required to be present in a dataset"""

    def __init__(self,
                 cells: list[pd.BatteryDataset | Path | str],
                 batch_size: int = 1,
                 required_data: list[str] = ('cycle_data', 'raw_data'),
                 random_seed: int | None = 1):
        super().__init__()
        self.batch_size = batch_size
        self.cells = list(cells)
        self.rng = np.random.default_rng(random_seed)
        self.required_data = required_data

    def __iter__(self) -> Iterator[tuple[InputType, OutputType | None]]:
        """Produce training data for the CNN

        Yields:
            - Input images for all batteries in batch
            - Capacity loss as a function of cycle
            - Mask of whether the capacity is actually measured for that cycle
        """

        for i in range(len(self.cells)):
            cell = self.load_cell(i)
            yield self.compute_inputs(cell), None

    def compute_inputs(self, cell: BatteryDataset) -> InputType:
        """Compute the features used as inputs

        Args:
            cell: Cell of interest
        Returns:
            Input features for that cell
        """

    def load_cell(self, i: int) -> BatteryDataset:
        """Get a particular cell from the dataset associated with this loader

        Args:
            i: Index of the cell
        Returns:
            BatteryDataset which is ensured to have the data from :attr:`required_data`
        """

        # Get the dataset
        if isinstance(self.cells[i], BatteryDataset):
            cell = self.cells[i]
        else:
            cell = BatteryDataset.from_batdata_hdf(self.cells[i], subsets=self.required_data)

        # Find which data are missing, if any
        for r in self.required_data:
            if getattr(cell, r) is None:
                raise ValueError(f'Cell {i} is missing data: {r}')
        return cell
