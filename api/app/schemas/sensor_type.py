from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SensorTypeBase(BaseModel):
    name: str = Field(max_length=100)
    unit: str = Field(max_length=50)
    description: str | None = Field(default=None, max_length=500)
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeCreate(SensorTypeBase):
    pass


class SensorTypeResponse(SensorTypeBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class SensorTypeUpdate(BaseModel):
    name: str | None = None
    unit: str | None = None
    description: str | None = None
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None
