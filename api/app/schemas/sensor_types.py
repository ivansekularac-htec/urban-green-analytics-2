from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.base import AuditModelBase


class SensorTypeBase(BaseModel):
    name: str = Field(max_length=100)
    unit: str = Field(max_length=50)
    description: str | None = Field(default=None, max_length=500)
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeCreate(SensorTypeBase):
    pass


class SensorTypeUpdate(BaseModel):
    name: str | None = None
    unit: str | None = None
    description: str | None = None
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeResponse(
    AuditModelBase,
    SensorTypeBase,
):
    pass
