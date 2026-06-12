from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class SensorTypeBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    unit: str = Field(
        min_length=1,
        max_length=50,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None


class SensorTypeCreate(SensorTypeBase):
    pass


class SensorTypeResponse(SensorTypeBase, BaseResponse):
    pass
