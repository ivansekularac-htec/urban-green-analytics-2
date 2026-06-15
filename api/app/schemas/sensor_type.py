from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SensorTypeBase(BaseModel):
    """Base schema for sensor type data."""

    name: str = Field(max_length=100)
    unit: str = Field(max_length=50)
    description: str | None = Field(max_length=500)
    optimal_min: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=3,
    )
    optimal_max: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=3,
    )


class SensorTypeCreate(SensorTypeBase):
    """Schema for creating a sensor type."""

    pass


class SensorTypeUpdate(BaseModel):
    """Schema for updating sensor type data."""

    name: str | None = Field(default=None, max_length=100)
    unit: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    optimal_min: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=3,
    )
    optimal_max: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=3,
    )


class SensorTypeResponse(SensorTypeBase):
    """Schema for returning sensor type data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
