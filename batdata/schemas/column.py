"""Schemas related to describing cycling data"""
from enum import Enum
from typing import List, Dict, Optional, Union, Any

from pydantic import BaseModel, Field, model_validator
from pandas import DataFrame


class ChargingState(str, Enum):
    """Potential charging states of the battery"""

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


class DataType(str, Enum):
    """Types available for columns"""
    FLOAT = "float"
    INTEGER = "integer"
    CONTROL = "control"
    STATE = "state"
    OTHER = "other"


class ColumnInfo(BaseModel):
    """Description of a column for a schema"""

    required: bool = False
    """Whether the column is required"""
    type: Union[DataType] = DataType.OTHER
    """Python type of the field (e.g., ``float``)"""
    description: str = ...
    """Human-readable description of the column"""
    units: Optional[str] = None
    """Units for the value, if applicable"""
    monotonic: bool = False
    """Whether the values should increase or remain constant between subsequent rows"""


class ColumnSchema(BaseModel, frozen=True):
    """Base class for schemas that describe the columns of a tabular dataset

    Implement a schema to be re-used across multiple datasets by creating a subclass and
    adding attributes for each expected column. The type of each attribute must be a :class:`ColumnInfo`
    with a default value that defines the
    """

    extra_columns: Dict[str, ColumnInfo] = Field(default_factory=dict)
    """Descriptions of columns beyond those defined in the batdata schema"""

    @property
    def columns(self) -> Dict[str, ColumnInfo]:
        """Map of name to description for all columns"""
        specified = dict((k, getattr(self, k)) for k in self.model_fields if k != "extra_columns")
        specified.update(self.extra_columns)
        return specified

    @property
    def column_names(self) -> List[str]:
        """Names of all columns defined in this schema"""
        specified = [x for x in self.model_fields if x != "extra_columns"]
        specified.extend(self.extra_columns)
        return specified

    @model_validator(mode='before')
    def _check_attributes(cls, d: Any):
        for field_name, field_info in cls.model_fields.items():
            if field_name == "extra_columns":
                continue
            elif field_info.annotation != ColumnInfo:
                raise ValueError('The subclass is incorrect. All fields must be `ColumnSchema`')
            elif field_info.default is None:
                raise ValueError('The subclass is incorrect. All fields must have a default value')
        return d

    def validate_dataframe(self, data: DataFrame, allow_extra_columns: bool = True):
        # Get the columns from the dataframe and their types
        data_columns = data.dtypes.to_dict()

        # If needed, check for extra columns
        if not allow_extra_columns:
            extra_cols = set(data_columns.keys()).difference(self.model_fields.keys()).difference(self.extra_columns.keys())
            if len(extra_cols) > 0:
                raise ValueError(f'Dataset contains extra columns: {" ".join(extra_cols)}')

        # Check each of the columns that match
        for column, col_schema in self.model_fields.items():
            col_schema = col_schema.default
            if column == 'extra_columns':
                continue

            # Check if column is missing
            if column not in data_columns:
                if col_schema.required:
                    raise ValueError(f'Dataset is missing a required column: {column}')
                continue

            # Check numeric data types
            actual_type = data_columns[column]
            col_type = col_schema.type
            if col_type == DataType.FLOAT:
                if actual_type.kind not in ['f', 'c']:
                    raise ValueError(f'Column {column} is a {actual_type} and not a floating point number')
            elif col_type == DataType.INTEGER:
                if actual_type.kind not in ['i', 'u']:
                    raise ValueError(f'Column {column} is a {actual_type} and not an integer')
            elif col_type in [DataType.CONTROL, DataType.STATE]:
                my_enum = {
                    DataType.CONTROL: ControlMethod,
                    DataType.STATE: ChargingState
                }[col_type]
                is_enum = data[column].isin(list(my_enum))
                bad = data[~is_enum][column]
                if len(bad) > 0:
                    raise ValueError(f'Column {column} contains values not in {my_enum}: {set(bad)}')
            elif col_type == DataType.OTHER:
                continue
            else:
                raise ValueError(f'No type checking for {col_type}')

            # Check if increasing
            if col_schema.monotonic:
                is_monotonic = all(y >= x for x, y in zip(data[column], data[column].iloc[1:]))
                if not is_monotonic:
                    raise ValueError(f'Column {column} is not monotonically increasing')


class RawData(ColumnSchema):
    """Schema for the time series data."""

    # Related to testing protocols
    file_number: ColumnInfo = ColumnInfo(description="Which file a row came from, if the data was originally split into multiple files",
                                         type=DataType.INTEGER, monotonic=True)

    # Control methods
    state: ColumnInfo = ColumnInfo(description="Whether the battery is being charged, discharged or otherwise.", type=DataType.STATE)
    method: ColumnInfo = ColumnInfo(description="Method to control the charge or discharge", type=DataType.CONTROL)
    cycle_number: ColumnInfo = ColumnInfo(description="Index of the testing cycle, starting at 0.", monotonic=True, type=DataType.INTEGER)
    step_index: ColumnInfo = ColumnInfo(description="Index of the step number within a testing cycle. A step change"
                                                    " is defined by a change states between charging, discharging, or resting.",
                                        type=DataType.INTEGER)
    substep_index: ColumnInfo = ColumnInfo(description="Change of the control method within a cycle.", type=DataType.INTEGER)

    # Required measurement data
    test_time: ColumnInfo = ColumnInfo(description="Time from the beginning of measurements", units='s', monotonic=True, type=DataType.FLOAT, required=True)
    voltage: ColumnInfo = ColumnInfo(description="Measured voltage of the system", units="V", type=DataType.FLOAT, required=True)
    current: ColumnInfo = ColumnInfo(description="Measured current of the system. Positive current represents the battery discharging.",
                                     units='A', required=True, type=DataType.FLOAT)
    internal_resistance: ColumnInfo = ColumnInfo(description="Internal resistance of the battery.", units="ohm", type=DataType.FLOAT)

    # Other measurement data
    time: ColumnInfo = ColumnInfo(description="Time as a UNIX timestamp.", units='s', monotonic=True, type=DataType.FLOAT)
    temperature: ColumnInfo = ColumnInfo(description="Temperature of the battery", units='C', type=DataType.FLOAT)

    # Derived data
    cycle_time: ColumnInfo = ColumnInfo(description="Time from the beginning of a cycle", units='s', monotonic=True, type=DataType.FLOAT)
    cycle_capacity: ColumnInfo = ColumnInfo(description="Cumulative change in amount of charge transferred from a battery since the start of a cycle. "
                                                        "Positive values indicate the battery has discharged since the start of the cycle.",
                                            type=DataType.FLOAT, units='A-hr')
    cycle_energy: ColumnInfo = ColumnInfo(description="Cumulative change in amount of energy transferred from a battery since the start of a cycle. "
                                                      "Positive values indicate the battery has discharged since the start of the cycle.",
                                          type=DataType.FLOAT, units='J')
    cycle_capacity_charge: ColumnInfo = ColumnInfo(description="Cycle capacity computed only during the 'charging' phase of a cycle",
                                                   units='A-hr', type=DataType.FLOAT)
    cycle_capacity_discharge: ColumnInfo = ColumnInfo(description="Cycle capacity computed only during the 'discharging' phase of a cycle",
                                                      units='A-hr', type=DataType.FLOAT)


class CycleLevelData(ColumnSchema):
    """Statistics about the performance of a cell over a certain cycle"""

    # Related to time
    cycle_number: ColumnInfo = ColumnInfo(description='Index of the cycle', monotonic=True, type=DataType.INTEGER, required=True)
    cycle_start: ColumnInfo = ColumnInfo(description='Time since the first data point recorded for this battery for the start of this cycle',
                                         units="s", monotonic=True, type=DataType.FLOAT)
    cycle_duration: ColumnInfo = ColumnInfo(description='Duration of this cycle', units='s', type=DataType.FLOAT)

    # Related to the total amount of energy or electrons moved
    capacity_discharge: ColumnInfo = ColumnInfo(description='Total amount of electrons released during discharge', units='A-hr', type=DataType.FLOAT)
    energy_discharge: ColumnInfo = ColumnInfo(description='Total amount of energy released during discharge', units='W-hr', type=DataType.FLOAT)
    capacity_charge: ColumnInfo = ColumnInfo(description='Total amount of electrons stored during charge', units='A-hr', type=DataType.FLOAT)
    energy_charge: ColumnInfo = ColumnInfo(description='Total amount of energy stored during charge', units='W-hr', type=DataType.FLOAT)
    coulomb_efficiency: ColumnInfo = ColumnInfo(description='Fraction of electric charge that is lost during charge and recharge',
                                                units='%', type=DataType.FLOAT)
    energy_efficiency: ColumnInfo = ColumnInfo(description='Amount of energy lost during charge and discharge', type=DataType.FLOAT)

    # Related to voltage
    discharge_V_average: ColumnInfo = ColumnInfo(description='Average voltage during discharging', units='V', type=DataType.FLOAT)
    charge_V_average: ColumnInfo = ColumnInfo(description='Average voltage during charge', units='V', type=DataType.FLOAT)
    V_maximum: ColumnInfo = ColumnInfo(description='Maximum voltage during cycle', units='V', type=DataType.FLOAT)
    V_minimum: ColumnInfo = ColumnInfo(description='Minimum voltage during cycle', units='V', type=DataType.FLOAT)

    # Related to current
    discharge_I_average: ColumnInfo = ColumnInfo(description='Average current during discharge', units='A', type=DataType.FLOAT)
    charge_I_average: ColumnInfo = ColumnInfo(description='Average current during charge', units='A', type=DataType.FLOAT)

    # Temperature
    temperature_minimum: ColumnInfo = ColumnInfo(description='Minimum observed battery temperature during cycle', units='C', type=DataType.FLOAT)
    temperature_maximum: ColumnInfo = ColumnInfo(description='Maximum observed battery temperature during cycle', units='C', type=DataType.FLOAT)
    temperature_average: ColumnInfo = ColumnInfo(description='Average observed battery temperature during cycle', units='C', type=DataType.FLOAT)
