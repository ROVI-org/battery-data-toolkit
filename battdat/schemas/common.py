"""Schemas used in multiple places"""
from typing import Literal

from pydantic import BaseModel, Field

class Dimensions(BaseModel):
    """Dimensions of a physical object"""

    shape: str = Field(..., description='Overall shape of an object')
    units: str = Field(..., description='Units for all dimensions')



class Cylinder(Dimensions):
    """Dimensions of a cylindrical object"""
    shape: Literal['cylinder'] = 'cylinder'
    radius: float = Field(..., description='Radius of the base')
    height: float = Field(..., description='Length of the cylinder')


class RectangularPrism(Dimensions):
    """Dimensions of a cylindrical object"""
    shape: Literal['rectangular'] = 'rectangular'
    length: float = Field(..., description='Length of one axis')
    width: float = Field(..., description='Radius of the base')
    height: float = Field(..., description='Length of the cylinder')
