"""Schemas associated with Electrochemical Impedance Spectroscopy"""
from pandas import DataFrame
import numpy as np

from .column import ColumnSchema, ColumnInfo, DataType


class EISData(ColumnSchema):
    """Measurements for a specific EIS test"""

    test_id: ColumnInfo = ColumnInfo(description='Integer used to identify rows belonging to the same experiment.', required=True, type=DataType.INTEGER)
    test_time: ColumnInfo = ColumnInfo(description="Time from the beginning of measurements.", units="s", monotonic=True, type=DataType.FLOAT)
    time: ColumnInfo = ColumnInfo(description="Time as a UNIX timestamp. Assumed to be in UTC", type=DataType.FLOAT)
    frequency: ColumnInfo = ColumnInfo(description="Applied frequency", units="Hz", required=True, type=DataType.FLOAT)
    z_real: ColumnInfo = ColumnInfo(description="Real component of impedance", units="Ohm", required=True, type=DataType.FLOAT)
    z_imag: ColumnInfo = ColumnInfo(description="Imaginary component of impedance", units="Ohm", required=True, type=DataType.FLOAT)
    z_mag: ColumnInfo = ColumnInfo(description="Magnitude of impedance", units="Ohm", required=True, type=DataType.FLOAT)
    z_phase: ColumnInfo = ColumnInfo(description="Phase angle of the impedance", units="Degree", required=True, type=DataType.FLOAT)

    def validate_dataframe(self, data: DataFrame, allow_extra_columns: bool = True):
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
