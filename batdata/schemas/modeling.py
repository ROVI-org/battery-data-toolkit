"""Metadata which describes how data produced by models were generated"""
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, AnyUrl


class ModelTypes(str, Enum):
    """Type of computational method"""

    physics = 'physics'
    """A computational application that uses a physical model to predict the behaviour of a system,
    providing a identifiable analogy with the original object.

    IRI: https://w3id.org/emmo#EMMO_8d4962d7_9608_44f7_a2f1_82a4bb173f4a"""
    data = 'data'
    """A computational application that uses existing data to predict the behaviour of a system
    without providing a identifiable analogy with the original object.

    IRI: https://w3id.org/emmo#EMMO_a4b14b83_9392_4a5f_a2e8_b2b58793f59b"""

    empirical = 'empirical'
    """A computational application that uses an empiric equation to predict the behaviour of a system
    without relying on the knowledge of the actual physical phenomena occurring in the object.

    IRI: https://w3id.org/emmo#EMMO_67c70dcd_2adf_4e6c_b3f8_f33dd1512487"""


class ModelMetadata(BaseModel, extra='allow'):
    """Describe the type and version of a computational tool used to generate battery data"""

    # High-level information about the code
    name: str = Field(..., description='Name of the software')
    version: Optional[str] = Field(..., description='Version of the software if known')
    type: Optional[ModelTypes] = Field(None, description='Type of the computational method it implements.')
    references: Optional[List[AnyUrl]] = Field(None, description='List of references associated with the software')

    # Details for physics based simulation
    models: Optional[List[str]] = Field(None, description='Type of mathematical model(s) being used in physics simulation.'
                                                          'Use terms defined in BattINFO, such as "BatteryEquivalentCircuitModel".',
                                        root_iri='https://w3id.org/emmo#EMMO_f7ed665b_c2e1_42bc_889b_6b42ed3a36f0')
    simulation_type: Optional[str] = Field(None, description='Type of simulation being performed. '
                                                             'Use terms defined in BattINFO, such as "TightlyCoupledModelsSimulation"',
                                           root_iri='https://w3id.org/emmo#EMMO_e97af6ec_4371_4bbc_8936_34b76e33302f')
