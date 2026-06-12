from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SensorTypeBase(BaseModel):
    name: str
    unit: str
    description: str | None = None
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeCreate(SensorTypeBase):
    pass


class SensorTypeResponse(SensorTypeBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
