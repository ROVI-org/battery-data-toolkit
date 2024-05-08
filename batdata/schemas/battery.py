"""Schemas associated with the components of a battery"""
from typing import Optional, List

from pydantic import BaseModel, Field


class ElectrodeDescription(BaseModel, extra='allow'):
    """Description of an electrode"""

    name: str = Field(..., description='Short description of the electrolyte type')

    # Relating to sourcing information
    supplier: Optional[str] = Field(None, description='Manufacturer of the material')
    product: Optional[str] = Field(None, description='Name of the product. Unique to the supplier')

    # Relating to the microstructure of the electrode
    thickness: Optional[float] = Field(None, description='Thickness of the material (units: μm)', ge=0)
    area: Optional[float] = Field(None, description='Total area of the electrode (units: cm2)', ge=0)
    loading: Optional[float] = Field(None, description='Amount of active material per area (units: mg/cm^2)', ge=0)
    porosity: Optional[float] = Field(None, description='Relative volume of the electrode occupied by gas (units: %)', ge=0, le=100)


class ElectrolyteAdditive(BaseModel, extra='allow'):
    """Additive to the electrolyte"""

    name: str = Field(..., description='Name of the additive')
    amount: Optional[float] = Field(None, description='Amount added to the solution')
    units: Optional[float] = Field(None, description='Units of the amount')


class ElectrolyteDescription(BaseModel, extra='allow'):
    """Description of the electrolyte"""

    name: str = Field(..., description='Short description of the electrolyte types')
    additives: List[ElectrolyteAdditive] = Field(default_factory=list, help='Any additives present in the electrolyte')


class BatteryDescription(BaseModel, extra='allow'):
    """Description of the entire battery"""

    # Overall design information
    manufacturer: str = Field(None, description="Manufacturer of the battery")
    design: str = Field(None, description="Name of the battery type, such as the battery product ID")

    # Geometry information
    layer_count: Optional[int] = Field(None, description="Number of layers within the battery", gt=1)

    # Materials description
    anode: Optional[ElectrodeDescription] = Field(None, description="Name of the anode material")
    cathode: Optional[ElectrodeDescription] = Field(None, description="Name of the cathode material")
    electrolyte: Optional[ElectrolyteDescription] = Field(None, description="Name of the electrolyte material")

    # Performance information
    nominal_capacity: float = Field(None, description="Rated capacity of the battery. Units: A-hr",
                                    iri="https://w3id.org/emmo/domain/electrochemistry#electrochemistry_9b3b4668_0795_4a35_9965_2af383497a26")
