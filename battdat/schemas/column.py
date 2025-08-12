"""Schemas related to describing cycling data"""
import json
from enum import Enum
from typing import List, Dict, Optional, Union, Any

from pydantic import BaseModel, Field, model_validator, create_model
from pandas import DataFrame


class ChargingState(str, Enum):
    """Potential charging states of the battery"""

    charging = "charging"
    rest = "resting"
    discharging = "discharging"
    unknown = "unknown"


class ControlMethod(str, Enum):
    """Method used to control battery during a certain step"""

    short_rest = "short_rest"
    """A very short rest period. Defined as a step with with near-zero current lasting for less than 30 seconds."""
    rest = "rest"
    """An extended period of neither charging nor discharging"""
    short_nonrest = "short_nonrest"
    """A very short period of charging or discharging.
    Defined as a step lasting for less than 30 seconds with a non-zero current, but with fewer than 5 data points."""
    pulse = "pulse"
    """A short period of a large current lasting for less than 30 seconds. Must contain at least 5 data points."""
    constant_current = "constant_current"
    """A step where the current is held constant"""
    constant_voltage = "constant_voltage"
    """A step where the voltage is held constant"""
    constant_power = "constant_power"
    """A step where the power is held constant"""
    unknown = "unknown"
    """A step where the control method is not known"""
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
    """Base class for schemas that describe the columns of a table

    Implement a schema to be re-used across multiple datasets by creating a subclass and
    adding attributes for each expected column. The type of each attribute must be a :class:`ColumnInfo`
    and have a default value.

    Save a Schema to disk in JSON format using :meth:`model_dump_json`.
    Load it using the :meth:`model_validate_json` method of the appropriate subclass,
    if you know the subclass, or :meth:`from_json`, if you do not.
    """

    extra_columns: Dict[str, ColumnInfo] = Field(default_factory=dict)
    """Descriptions of columns beyond those defined in the schema"""

    def __getitem__(self, item: str) -> ColumnInfo:
        """Retrieve a specific column"""

        if item in self.extra_columns:
            return self.extra_columns[item]
        elif hasattr(self, item):
            return getattr(self, item)
        else:
            raise KeyError(item)

    def __contains__(self, item):
        return item in self.extra_columns or hasattr(self, item)

    @property
    def columns(self) -> Dict[str, ColumnInfo]:
        """Map of name to description for all columns"""
        specified = dict((k, getattr(self, k)) for k in self.__class__.model_fields if k != "extra_columns")
        specified.update(self.extra_columns)
        return specified

    @property
    def column_names(self) -> List[str]:
        """Names of all columns defined in this schema"""
        specified = [x for x in self.__class__.model_fields if x != "extra_columns"]
        specified.extend(self.extra_columns.keys())
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

    def add_column(self,
                   name: str,
                   description: str,
                   data_type: DataType = DataType.OTHER,
                   required: bool = False,
                   units: Optional[str] = None,
                   monotonic: bool = False) -> ColumnInfo:
        """Add a new column to the :attr:`extra_columns` as a :class:`ColumnInfo` object

        Args:
            name: Name of new column
            description: Human-readable description of the data
            data_type: Type of data
            required: Whether the data must be included in a table
            units: Units used for all rows in column
            monotonic: Whether values must always remain constant or increase
        Returns:
            The new column object
        """
        new_col = ColumnInfo(
            description=description, required=required, units=units, monotonic=monotonic, type=data_type
        )
        self.extra_columns[name] = new_col
        return new_col

    def validate_dataframe(self, data: DataFrame, allow_extra_columns: bool = True):
        """Check whether a dataframe matches this schema

        Args:
            data: DataFrame to be assessed
            allow_extra_columns: Whether to raise an error if the dataframe contains
                columns which are not defined in this schema.
        Raises:
            (ValueError) If the dataframe does not adhere
        """
        # Get the columns from the dataframe and their types
        data_columns = data.dtypes.to_dict()

        # If needed, check for extra columns
        if not allow_extra_columns:
            extra_cols = set(data_columns.keys()).difference(self.column_names)
            if len(extra_cols) > 0:
                raise ValueError(f'Dataset contains extra columns: {" ".join(extra_cols)}')

        # Check each of the columns that match
        for column, col_schema in self.columns.items():
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

    @classmethod
    def from_json(cls, buf: str) -> 'ColumnSchema':
        """Read a JSON description of a column schema into an object

        The object will not have the same class as the original, but will
        have the same column information.

        Args:
            buf: JSON version of this class
        Returns:
            Model as a subclass of :class:`ColumnSchema`
        """

        data = json.loads(buf)
        extra_cols = dict((k, ColumnInfo.model_validate(v)) for k, v in data.pop('extra_columns', {}).items())
        my_cols = dict((k, (ColumnInfo, ColumnInfo.model_validate(v))) for k, v in data.items())

        return create_model(
            'ParsedColumnSchema',
            **my_cols,
            extra_columns=(Dict[str, ColumnInfo], extra_cols),
            __base__=cls,
        )()


class RawData(ColumnSchema):
    """Data describing measurements of a single cell"""

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
    current: ColumnInfo = ColumnInfo(description="Measured current of the system. Positive current represents the battery charging.",
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
    """Statistics about the performance of a cell over entire cycles"""

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
    max_cycled_capacity: ColumnInfo = ColumnInfo(description='Maximum amount of charge cycled during cycle',
                                                 units='A-hr',
                                                 type=DataType.FLOAT)

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
