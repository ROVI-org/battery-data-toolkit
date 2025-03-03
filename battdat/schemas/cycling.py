"""Describing cycling protocol"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class CyclingProtocol(BaseModel, extra='allow'):
    """Test protocol for cell cycling"""
    cycler: Optional[str] = Field(None, description='Name of the cycling machine')
    start_date: Optional[date] = Field(None, description="Date the initial test on the cell began")
    set_temperature: Optional[float] = Field(None, description="Set temperature for the battery testing equipment",
                                             json_schema_extra=dict(units='C'))
    schedule: Optional[str] = Field(None, description="Schedule file used for the cycling machine")
