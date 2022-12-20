"""Schemas for battery data and metadata"""
from datetime import date
from typing import List, Tuple, Dict
from enum import Enum

from pandas import DataFrame
from pydantic import BaseModel, Field, AnyUrl


class BatteryMetadata(BaseModel):
    """Representation for the metadata about a battery

    The metadata captures the information about what experiment was run
    on what battery. A complete set of metadata should be sufficient to
    reproduce an experiment.
    """

    # TODO (wardlt): Expand on these fields in consultation with battery data working group
    # Miscellaneous fields
    name: str = Field(None, description="Name of the cell. Any format for the name is acceptable,"
                                        " as it is intended to be used by the battery data provider.")
    comments: str = Field(None, description="Long form comments describing the test")

    # Fields that describe the test protocol
    cycler: str = Field(None, description='Name of the cycling machine')
    start_date: date = Field(None, description="Date the initial test on the cell began")
    set_temperature: float = Field(None, description="Set temperature for the battery testing equipment. Units: C")
    schedule: str = Field(None, description="Schedule file used for the cycling machine")

    # Field that describe the battery
    # TODO (wardlt): Needs a more thorough description, see UW's work
    manufacturer: str = Field(None, description="Manufacturer of the battery")
    design: str = Field(None, description="Name of the battery type, such as the battery product ID")
    anode: str = Field(None, description="Name of the anode material")
    cathode: str = Field(None, description="Name of the cathode material")
    electrolyte: str = Field(None, description="Name of the electrolyte material")
    nominal_capacity: float = Field(None, description="Rated capacity of the battery. Units: Ah")

    # Fields that describe the source of data
    # TODO (wardlt): Consult Ben about whether we should use DataCite
    source: str = Field(None, description="Organization who created this data")
    dataset_name: str = Field(None, description="Name of a larger dataset this data is associated with")
    authors: List[Tuple[str, str]] = Field(None, description="Name and affiliation of each of the authors of the data")
    associated_ids: List[AnyUrl] = Field(None, description="Any identifiers associated with this data file."
                                                           " Identifiers can be any URI, such as DOIs of associated"
                                                           " paper or HTTP addresses of associated websites")

    # Generic metadata
    other: Dict = Field(default_factory=dict, help="Any other useful run information")


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


class CyclingData(BaseModel):
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
                                                     "monotonically increasing", ge=0, monotonic=True)
    test_time: List[float] = Field(..., description="Time from the beginning of the cycling test. Times must be "
                                                    "nonnegative and monotonically increasing. Units: s",
                                   monotonic=True)
    voltage: List[float] = Field(..., description="Measured voltage of the system. Units: V")
    current: List[float] = Field(..., description="Measured current of the system. Positive current represents "
                                                  "the battery discharging and negative represents the battery"
                                                  "charging. Units: A")
    state: List[ChargingState] = Field(None, description="Determination of whether the battery is being charged, "
                                                         "discharged or held at a constant charge")
    method: List[ControlMethod] = Field(None, description="List of the method used to control the battery system")
    temperature: List[float] = Field(None, description="Temperature of the battery. Units: C")
    internal_resistance: List[float] = Field(None, description="Internal resistance of the battery. Units: ohm")
    substep_index: List[int] = Field(None, description="Index of the substep within a testing cycle. A substep"
                                                       " change is defined by a change of the charging or discharging"
                                                       " method, such as change from constant voltage to"
                                                       " constant current")
    # TODO (wardlt): Consult battery data working group on whether they support the definitions listed here and
    #  whether they have any additional fields they would recommend standardizing

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
                col_type = schema['definitions'][ref_name]['type']
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
