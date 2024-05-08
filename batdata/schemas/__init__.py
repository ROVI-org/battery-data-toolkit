"""Schemas for battery data and metadata"""
from datetime import date
from typing import List, Tuple, Optional, Dict

from pydantic import BaseModel, Field, AnyUrl

from batdata.schemas.modeling import ModelMetadata
from batdata.schemas.battery import BatteryDescription
from batdata.version import __version__


class BatteryMetadata(BaseModel, extra='allow'):
    """Representation for the metadata about a battery

    The metadata captures the information about what experiment was run
    on what battery. A complete set of metadata should be sufficient to
    reproduce an experiment.
    """

    # Miscellaneous fields
    name: Optional[str] = Field(None, description="Name of the cell. Any format for the name is acceptable,"
                                                  " as it is intended to be used by the battery data provider.")
    comments: Optional[str] = Field(None, description="Long form comments describing the test")
    version: str = Field(__version__, description="Version of this metadata. Set by the battery-data-toolkit")
    is_measurement: bool = Field(True, description="Whether the data was created observationally as opposed to a computer simulation",
                                 iri="https://w3id.org/emmo#EMMO_463bcfda_867b_41d9_a967_211d4d437cfb")

    # Fields that describe the test protocol
    cycler: Optional[str] = Field(None, description='Name of the cycling machine')
    start_date: Optional[date] = Field(None, description="Date the initial test on the cell began")
    set_temperature: Optional[float] = Field(None, description="Set temperature for the battery testing equipment. Units: C")
    schedule: Optional[str] = Field(None, description="Schedule file used for the cycling machine")

    # Field that describe the battery assembly
    battery: Optional[BatteryDescription] = Field(None, description="Description of the battery being tested")

    # Fields that describe source of synthetic data
    modeling: Optional[ModelMetadata] = Field(None, description="Description of simulation approach")

    # Fields that describe the source of data
    source: Optional[str] = Field(None, description="Organization who created this data")
    dataset_name: Optional[str] = Field(None, description="Name of a larger dataset this data is associated with")
    authors: Optional[List[Tuple[str, str]]] = Field(None, description="Name and affiliation of each of the authors of the data. First and last names")
    associated_ids: Optional[List[AnyUrl]] = Field(None, description="Any identifiers associated with this data file."
                                                                     " Identifiers can be any URI, such as DOIs of associated"
                                                                     " paper or HTTP addresses of associated websites")

    # Description of additional columns
    raw_data_columns: Dict[str, str] = Field(default_factory=dict, description='Descriptions of non-standard columns in the raw data')
    cycle_stats_columns: Dict[str, str] = Field(default_factory=dict, description='Descriptions of non-standard columns in the cycle stats')
    eis_data_columns: Dict[str, str] = Field(default_factory=dict, description='Descriptions of non-standard columns in the EIS data')
