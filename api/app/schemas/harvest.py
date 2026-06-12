from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class HarvestBase(BaseModel):
    """Base schema for harvest data."""

    farm_id: int
    crop_id: int
    quality_grade_id: int
    weight_kg: Decimal


class HarvestCreate(HarvestBase):
    """Schema for creating a harvest record."""

    pass


class HarvestResponse(HarvestBase):
    """Schema for returning harvest data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
