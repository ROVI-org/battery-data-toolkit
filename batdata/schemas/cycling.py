"""Schemas related to describing cycling data"""
from enum import Enum
from typing import List

from pydantic import BaseModel, Field
from pandas import DataFrame


class ChargingState(str, Enum):
    """Potential charging states of the battery:

    - ``charging``: Battery is being charged
    - ``hold``: Battery is neither charging nor discharging
    - ``discharging``: Battery is being discharged
    - ``unknown``: State was unable to be determined
    """

    charging = "charging"
    hold = "hold"
    discharging = "discharging"
    unknown = "unknown"


class ControlMethod(str, Enum):
    """Method used to control battery during a certain step

    - ``short_rest``: A very short rest period. Defined as a step with 4 or fewer measurements with near-zero current
    - ``rest``: An extended period of neither charging nor discharging
    - ``short_nonrest``: A very short period of charging or discharging. Defined as a step with 4 or fewer measurements
        with at least one non-zero current.
    - ``constant_current``: A step where the current is held constant
    - ``constant_voltage``: A step where the voltage is held constant
    - ``other``: A step that does not fit into any of the predefined categories
    """

    short_rest = "short_rest"
    rest = "rest"
    short_nonrest = "short_nonrest"
    constant_current = "constant_current"
    constant_voltage = "constant_voltage"
    constant_power = "constant_power"
    pulse = "pulse"
    other = "other"


class ColumnSchema(BaseModel):
    """Base class for schemas that describe the columns of a tabular dataset"""

    @classmethod
    def validate_dataframe(cls, data: DataFrame, allow_extra_columns: bool = True):
        """Validate whether a DataFrame fits the target schema

        Parameters
        ----------
        data: DataFrame
            DataFrame to be validated
        allow_extra_columns: bool
            Whether to allow columns that are not defined in schema

        Raises
        ------
        ValueError
            If the dataset fails to validate
        """
        # Get the columns from the schema
        schema = cls.schema()
        schema_columns = schema['properties']
        required_cols = schema['required']

        # Get the columns from the dataframe and their types
        data_columns = data.dtypes.to_dict()

        # If needed, check for extra columns
        if not allow_extra_columns:
            extra_cols = set(data_columns.keys()).difference(schema_columns.keys())
            if len(extra_cols) > 0:
                raise ValueError(f'Dataset contains extra columns: {" ".join(extra_cols)}')

        # Check each of the columns that match
        for column, col_schema in schema_columns.items():
            # Check if column is missing
            if column not in data_columns:
                if column in required_cols:
                    raise ValueError(f'Dataset is missing a required column: {column}')
                continue

            # Get the data type for the column
            if '$ref' in col_schema['items']:
                ref_name = col_schema['items']['$ref'].split("/")[-1]
                col_type = schema['$defs'][ref_name]['type']
            else:
                col_type = col_schema['items']['type']

            # Check data types
            actual_type = data_columns[column]
            if col_type == "number":
                if actual_type.kind not in ['f', 'c']:
                    raise ValueError(f'Column {column} is a {actual_type} and not a floating point number')
            elif col_type == "integer":
                if actual_type.kind not in ['i', 'u']:
                    raise ValueError(f'Column {column} is a {actual_type} and not an integer')
            elif col_type == "string":
                if actual_type.kind not in ['S', 'U', 'O']:
                    raise ValueError(f'Column {column} is a {actual_type} and not a string')

            # Check enums
            enum_values = col_schema['items'].get('enum', None)
            if enum_values is not None:
                is_enum = data[column].isin(enum_values)
                bad = data[~is_enum][column]
                if len(bad) > 0:
                    raise ValueError(f'Column {column} contains values not in enum: {set(bad)}')

            # Check if increasing
            if col_schema.get('monotonic', False):
                is_monotonic = all(y >= x for x, y in zip(data[column], data[column].iloc[1:]))
                if not is_monotonic:
                    raise ValueError(f'Column {column} is not monotonically increasing')


class RawData(ColumnSchema):
    """Schema for the battery testing data.

    Each attribute in this array specifies columns within a :class:`BatteryDataFrame`.
    The schema is defined such that extra columns are allowed by default.
    The columns listed here represent those types of data for which we specify
    a common definition.
    """

    cycle_number: List[int] = Field(None, description="Index of the testing cycle. All indices should be"
                                                      " nonnegative and be monotonically increasing", monotonic=True)
    step_index: List[int] = Field(None, description="Index of the step number within a testing cycle. A step change"
                                                    " is defined by a change states between charging, discharging,"
                                                    " or resting.")
    file_number: List[int] = Field(None, description="Used if test data is stored in multiple files. Number represents "
                                                     "the index of the file. All indices should be nonnegative and "
                                                     "monotonically increasing", monotonic=True)
    test_time: List[float] = Field(..., description="Time from the beginning of the cycling test. Times must be "
                                                    "nonnegative and monotonically increasing. Units: s",
                                   monotonic=True)
    time: List[float] = Field(None, description="Time as a UNIX timestamp. Assumed to be in UTC")
    voltage: List[float] = Field(..., description="Measured voltage of the system. Units: V")
    current: List[float] = Field(..., description="Measured current of the system. Positive current represents "
                                                  "the battery discharging and negative represents the battery"
                                                  "charging. Units: A")
    state: List[ChargingState] = Field(None, description="Determination of whether the battery is being charged, "
                                                         "discharged or held at a constant charge")
    method: List[ControlMethod] = Field(None, description="List of the method used to control "
                                                          "the battery system")
    temperature: List[float] = Field(None, description="Temperature of the battery. Units: C")
    internal_resistance: List[float] = Field(None, description="Internal resistance of the battery. Units: ohm")
    substep_index: List[int] = Field(None, description="Index of the substep within a testing cycle. A substep"
                                                       " change is defined by a change of the charging or discharging"
                                                       " method, such as change from constant voltage to"
                                                       " constant current")


class CycleLevelData(ColumnSchema):
    """Statistics about the performance of a cell over a certain cycle"""

    # Related to time
    cycle_number: List[int] = Field(..., description='Index of the cycle', monotonic=True)
    cycle_start: List[float] = Field(None, description='Time since the first data point recorded for this battery for the start of this cycle. Units: s')
    cycle_duration: List[float] = Field(None, description='Duration of this cycle. Units: s')

    # Related to the total amount of energy or electrons moved
    discharge_capacity: List[float] = Field(None, description='Total amount of electrons moved during discharge. Units: A-hr')
    discharge_energy: List[float] = Field(None, description='Total amount of energy released during discharge. Units: W-hr')
    charge_capacity: List[float] = Field(None, description='Total amount of electrons moved during charge. Units: A-hr')
    charge_energy: List[float] = Field(None, description='Total amount of energy stored during charge. Units: W-hr')
    coulomb_efficiency: List[float] = Field(None, description='Fraction of electrons that are lost during charge and recharge. Units: %')
    energy_efficiency: List[float] = Field(None, description='Amount of energy lost during charge and discharge')

    # Related to voltage
    discharge_V_average: List[float] = Field(None, description='Average voltage during discharging. Units: V')
    charge_V_average: List[float] = Field(None, description='Average voltage during charge. Units: V')
    V_maximum: List[float] = Field(None, description='Maximum voltage during cycle. Units: V')
    V_minimum: List[float] = Field(None, description='Minimum voltage during cycle. Units: V')

    # Related to current
    discharge_I_average: List[float] = Field(None, description='Average current during discharge. Units: A')
    charge_I_average: List[float] = Field(None, description='Average current during charge. Units: A')

    # Temperature
    temperature_minimum: List[float] = Field(None, description='Minimum observed battery temperature during cycle. Units: C')
    temperature_maximum: List[float] = Field(None, description='Maximum observed battery temperature during cycle. Units: C')
    temperature_average: List[float] = Field(None, description='Average observed battery temperature during cycle. Units: C')
