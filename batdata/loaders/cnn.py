"""Data loaders used with convolutional neural networks"""
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from batdata.data import BatteryDataset
from batdata.loaders.base import BaseBatteryLoader, InputType, OutputType


class SaxenaLoader(BaseBatteryLoader[np.ndarray, np.ndarray]):
    """Provides the functionality for generating inputs and outputs in the format
    required for our CNN model

    - *Input*: A 2D matrix of discharge capacity at fixed voltage intervals
               for each cycle being used in the training set
    - *Output*: The observed capacity fade starting at the first cycle
                after that used for the training set

    Args:
        batch_size: Number of batteries to use per batch
        voltage_range: Minimum and maximum voltage for the input features
        voltage_steps: Number of voltage steps for the input vary
        random_seed: Random seed for generating batches
    """

    def __init__(self,
                 cells: list[pd.BatteryDataset | Path | str],
                 batch_size: int,
                 voltage_range: tuple[float, float] = (2.0, 3.5),
                 voltage_steps: int = 128,
                 random_seed: int | None = 1):
        super().__init__(
            cells=cells,
            batch_size=batch_size,
            random_seed=1
        )
        self.voltage_range = tuple(sorted(voltage_range))
        self.voltage_steps = voltage_steps
        self.rng = np.random.default_rng(random_seed)

    def __iter__(self) -> Iterator[tuple[InputType, OutputType | None]]:
        """Produce training data for the CNN

        Yields:
            - Input images for all batteries in batch
            - Capacity loss as a function of cycle
            - Mask of whether the capacity is actually measured for that cycle
        """
        raise NotImplemented()

    def compute_inputs(self, cell: BatteryDataset) -> InputType:

        # Get the input and initialize output
        n_cycles = 4
        output = np.zeros((4, self.voltage_steps))

        # Interpolate each cycle
        voltage_steps = np.linspace(*self.voltage_range, self.voltage_steps)
        for cid, cycle in cell.query(f'cycle_index < {n_cycles}').groupby('cycle_index'):
            min_cap = cycle['discharge_capacity'].min()
            max_cap = cycle['discharge_capacity'].max()
            output[cid, :] = interp1d(cycle['voltage'], cycle['discharge_capacity'], bounds_error=False, fill_value=(max_cap, min_cap))(voltage_steps)
        return output

    def generate_output_vector(self, ind: int, n_cycles: int) -> OutputType:
        """Generate the output vector of discharge capacities

        Args:
            ind: Index of battery
            n_cycles: Start cycle for reporting the capacity
        Returns:
            A 1D matrix of the appropriate number of remaining cycles
        """
        cell = self.summaries[ind]
        return cell['discharge_capacity'].iloc[n_cycles:] - cell['discharge_capacity'].iloc[n_cycles]
