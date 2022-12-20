"""Schemas for battery data and metadata"""
from datetime import date
from typing import List, Tuple, Optional

from pydantic import BaseModel, Field, AnyUrl, Extra

from batdata.schemas.battery import BatteryDescription
from batdata.version import __version__


class BatteryMetadata(BaseModel, extra=Extra.allow):
    """Representation for the metadata about a battery

    The metadata captures the information about what experiment was run
    on what battery. A complete set of metadata should be sufficient to
    reproduce an experiment.
    """

    # Miscellaneous fields
    name: str = Field(None, description="Name of the cell. Any format for the name is acceptable,"
                                        " as it is intended to be used by the battery data provider.")
    comments: str = Field(None, description="Long form comments describing the test")
    version: str = Field(__version__, description="Version of this metadata")

    # Fields that describe the test protocol
    cycler: str = Field(None, description='Name of the cycling machine')
    start_date: date = Field(None, description="Date the initial test on the cell began")
    set_temperature: float = Field(None, description="Set temperature for the battery testing equipment. Units: C")
    schedule: str = Field(None, description="Schedule file used for the cycling machine")

    # Field that describe the battery assembly
    battery: Optional[BatteryDescription] = Field(None, description="Description of the battery being tested")

    # Fields that describe the source of data
    source: str = Field(None, description="Organization who created this data")
    dataset_name: str = Field(None, description="Name of a larger dataset this data is associated with")
    authors: List[Tuple[str, str]] = Field(None, description="Name and affiliation of each of the authors of the data. First and last names")
    associated_ids: List[AnyUrl] = Field(None, description="Any identifiers associated with this data file."
                                                           " Identifiers can be any URI, such as DOIs of associated"
                                                           " paper or HTTP addresses of associated websites")
