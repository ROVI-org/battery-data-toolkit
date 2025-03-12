"""Metadata describing a battery system"""
from typing import Optional

from pydantic import BaseModel, Field

from .battery import BatteryDescription
from .common import Dimensions


class SystemDescription(BaseModel, allow_extras=True):
    """Metadata for a battery system which includes multiple racks of modules"""

    # High-level description of the system
    name: str = Field(..., description="Simple description of the battery")
    rated_power: Optional[float] = Field(..., description="Nameplate power of the system (units: kVA)")
    rated_energy: Optional[float] = Field(..., description="Nameplate power of the system (units: kWh)")

    # Operation limits for the system
    operating_temperature_min: Optional[float] = Field(..., description='Minimum suggested operation temperature. (units: C)')
    operating_temperature_max: Optional[float] = Field(..., description='Maximum suggested operation temperature. (units: C)')
    soc_limit_min: Optional[float] = Field(..., description='Minimum suggested state of charge. (units: %)')
    soc_limit_max: Optional[float] = Field(..., description='Maximum suggested state of charge. (units: %)')


class PowerConversionSpecification(BaseModel, allow_extras=True):
    """Specification of the Power Conversion System Between Battery and external grid"""

    pass


class RackSpecification(BaseModel, allow_extras=True):
    cell_spec: BatteryDescription = Field(default_factory=BatteryDescription,
                                          description='Description of individual cells within the assembly')

    dimensions: Optional[Dimensions] = Field(description='Physical extent of the rack')
