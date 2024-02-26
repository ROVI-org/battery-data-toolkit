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
        z_real_from_polar = np.multiply(data['z_mag'], np.cos(np.deg2rad(data['z_phase'])))
        z_imag_from_polar = np.multiply(data['z_mag'], np.sin(np.deg2rad(data['z_phase'])))
        if not np.isclose(z_real_from_polar, data['z_real'], rtol=0.01).all():
            raise ValueError('Polar and cartesian forms of impedance disagree for real component')
        if not np.isclose(z_imag_from_polar, data['z_imag'], rtol=0.01).all():
            raise ValueError('Polar and cartesian forms of impedance disagree for imaginary component')
