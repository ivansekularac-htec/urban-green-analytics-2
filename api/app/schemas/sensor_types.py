from decimal import Decimal

from pydantic import BaseModel

from app.schemas.base import AuditModelBase


class SensorTypeBase(BaseModel):
    name: str
    unit: str
    description: str | None = None
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeCreate(SensorTypeBase):
    pass


class SensorTypeResponse(
    AuditModelBase,
    SensorTypeBase,
):
    pass