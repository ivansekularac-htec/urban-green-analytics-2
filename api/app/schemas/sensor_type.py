from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import TimestampResponse


class SensorTypeBase(BaseModel):
    """Base schema for sensor type data."""

    name: str = Field(max_length=100)
    unit: str = Field(max_length=50)
    description: str | None = Field(default=None, max_length=500)
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeCreate(SensorTypeBase):
    """Schema used for sensor type creation."""

    pass


class SensorTypeUpdate(BaseModel):
    """Schema used for partial sensor type updates."""

    name: str | None = Field(default=None, max_length=100)
    unit: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeResponse(SensorTypeBase, TimestampResponse):
    """Schema returned when retrieving sensor type information."""

    pass
