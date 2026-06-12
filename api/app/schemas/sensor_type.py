from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SensorTypeBase(BaseModel):
    """Base schema for sensor type data."""

    name: str
    unit: str
    description: str | None = None
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeCreate(SensorTypeBase):
    """Schema for creating a sensor type."""

    pass


class SensorTypeResponse(SensorTypeBase):
    """Schema for returning sensor type data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
