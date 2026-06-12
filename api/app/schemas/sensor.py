"""
schemas/sensor.py
Pydantic schemas for sensor and sensor type models.
"""

from decimal import Decimal

from pydantic import BaseModel, Field

from app.models import SensorStatus
from app.schemas.base import AuditModelBase


class SensorTypeBase(BaseModel):
    """Base schema for sensor types."""

    name: str = Field(..., max_length=100)
    unit: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=500)
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeCreate(SensorTypeBase):
    """Schema for creating a sensor type."""

    pass


class SensorTypeUpdate(BaseModel):
    """Schema for updating a sensor type."""

    name: str | None = Field(None, max_length=100)
    unit: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=500)
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeResponse(AuditModelBase, SensorTypeBase):
    """Schema for sensor type response."""

    pass


class SensorBase(BaseModel):
    """Base schema for sensors."""

    farm_id: int
    sensor_type_id: int
    serial_number: str = Field(..., max_length=255)
    status: SensorStatus = SensorStatus.ACTIVE
    installed_at: int | None = None


class SensorCreate(SensorBase):
    """Schema for creating a sensor."""

    pass


class SensorUpdate(BaseModel):
    """Schema for updating a sensor."""

    farm_id: int | None = None
    sensor_type_id: int | None = None
    serial_number: str | None = Field(None, max_length=255)
    status: SensorStatus | None = None
    installed_at: int | None = None


class SensorResponse(AuditModelBase, SensorBase):
    """Schema for sensor response."""

    pass
