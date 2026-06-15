from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class HarvestBase(BaseModel):
    """Base schema for harvest data."""

    farm_id: int
    crop_id: int
    quality_grade_id: int
    weight_kg: Decimal = Field(
        default=None,
        max_digits=10,
        decimal_places=3,
    )


class HarvestCreate(HarvestBase):
    """Schema for creating a harvest record."""

    pass


class HarvestUpdate(BaseModel):
    """Schema for updating harvest data."""

    farm_id: int | None = None
    crop_id: int | None = None
    quality_grade_id: int | None = None
    weight_kg: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=3,
    )


class HarvestResponse(HarvestBase):
    """Schema for returning harvest data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
