from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import TimestampResponse


class HarvestBase(BaseModel):
    """Base schema for harvest data."""

    farm_id: int
    crop_id: int
    quality_grade_id: int
    weight_kg: Decimal = Field(gt=0)


class HarvestCreate(HarvestBase):
    """Schema used for creating harvest data."""

    pass


class HarvestUpdate(BaseModel):
    """Schema used for updating harvest data."""

    farm_id: int | None = None
    crop_id: int | None = None
    quality_grade_id: int | None = None
    weight_kg: Decimal | None = None


class HarvestResponse(HarvestBase, TimestampResponse):
    """Schema returned when retrieving harvest data."""

    pass
