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
    thickness: Optional[float] = Field(None, description='Thickness of the material', ge=0,
                                       json_schema_extra=dict(units='um'))
    area: Optional[float] = Field(None, description='Total area of the electrode', ge=0,
                                  json_schema_extra=dict(units='cm^2'))
    loading: Optional[float] = Field(None, description='Amount of active material per area', ge=0,
                                     json_schema_extra=dict(units='mg/cm^2'))
    porosity: Optional[float] = Field(None, description='Relative volume of the electrode occupied by gas',
                                      ge=0, le=100, json_schema_extra=dict(units='%'))


class ElectrolyteAdditive(BaseModel, extra='allow'):
    """Additive to the electrolyte"""

    name: str = Field(..., description='Name of the additive')
    amount: Optional[float] = Field(None, description='Amount added to the solution')
    units: Optional[float] = Field(None, description='Units of the amount')


class ElectrolyteDescription(BaseModel, extra='allow'):
    """Description of the electrolyte"""

    name: str = Field(..., description='Short description of the electrolyte types')
    additives: List[ElectrolyteAdditive] = Field(default_factory=list,
                                                 description='Any additives present in the electrolyte')


class BatteryDescription(BaseModel, extra='allow'):
    """Description of the entire battery"""

    # Overall design information
    manufacturer: Optional[str] = Field(None, description="Manufacturer of the battery")
    design: Optional[str] = Field(None, description="Name of the battery type, such as the battery product ID")

    # Geometry information
    layer_count: Optional[int] = Field(None, description="Number of layers within the battery", gt=1)
    form_factor: Optional[str] = Field(None, description="The general shape of the battery",
                                       json_schema_extra=dict(
                                           iri="https://w3id.org/emmo/domain/electrochemistry#electrochemistry_1586ef26_6d30_49e3_ae32_b4c9fc181941"
                                       ))
    mass: Optional[float] = Field(None, description="Mass of the entire battery",
                                  json_schema_extra=dict(units='kg'))
    dimensions: Optional[str] = Field(None, description='Dimensions of the battery in plain text.')

    # Materials description
    anode: Optional[ElectrodeDescription] = Field(None, description="Name of the anode material",
                                                  json_schema_extra=dict(
                                                      iri="https://w3id.org/emmo/domain/electrochemistry#electrochemistry_b6319c74_d2ce_48c0_a75a_63156776b302"
                                                  ))
    cathode: Optional[ElectrodeDescription] = Field(
        None, description="Name of the cathode material",
        json_schema_extra=dict(
            iri="https://w3id.org/emmo/domain/electrochemistry#electrochemistry_35c650ab_3b23_4938_b312_1b0dede2e6d5"
        ))
    electrolyte: Optional[ElectrolyteDescription] = Field(
        None, description="Name of the electrolyte material",
        json_schema_extra=dict(
            iri="https://w3id.org/emmo/domain/electrochemistry#electrochemistry_fb0d9eef_92af_4628_8814_e065ca255d59"
        ))

    # Performance information
    nominal_capacity: Optional[float] = Field(
        None, description="Rated capacity of the battery",
        json_schema_extra=dict(
            iri="https://w3id.org/emmo/domain/electrochemistry#electrochemistry_9b3b4668_0795_4a35_9965_2af383497a26",
            units='A-hr'
        ))
