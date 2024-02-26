"""Schemas associated with Electrochemical Impedance Spectroscopy"""

from typing import List

from pandas import DataFrame
from pydantic import Field
import numpy as np

from .cycling import ColumnSchema


class EISData(ColumnSchema):
    """Measurements for a specific EIS test"""

    test_time: List[float] = Field(None, description="Time from the beginning of the cycling test. Times must be "
                                                     "nonnegative and monotonically increasing. Units: s",
                                   monotonic=True)
    time: List[float] = Field(None, description="Time as a UNIX timestamp. Assumed to be in UTC")
    frequency: List[float] = Field(..., description="Applied frequency. Units: Hz")
    z_real: List[float] = Field(..., description="Real component of impedance. Units: Ohm")
    z_imag: List[float] = Field(..., description="Imaginary component of impedance. Units: Ohm")
    z_mag: List[float] = Field(..., description="Magnitude of impedance. Units: Ohm")
    z_phase: List[float] = Field(..., description="Phase angle of the impedance. Units: Degree")

    @classmethod
    def validate_dataframe(cls, data: DataFrame, allow_extra_columns: bool = True):
        # Check that the schema is supported
        super().validate_dataframe(data, allow_extra_columns)

        # Ensure that the cartesian coordinates for the impedance agree with the magnitude
        cart = {
            'real': np.multiply(data['z_mag'], np.cos(np.deg2rad(data['z_phase']))),
            'imag': np.multiply(data['z_mag'], np.sin(np.deg2rad(data['z_phase'])))
        }
        for k, values in cart.items():
            largest_diff = (np.abs(values - data[f'z_{k}']) / np.clip(values, a_min=1e-6, a_max=None)).max()
            if largest_diff > 0.01:
                raise ValueError(f'Polar and cartesian forms of impedance disagree for {k} component. Largest difference: {largest_diff * 100:.1f}%')
