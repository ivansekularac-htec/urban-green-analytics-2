"""
schemas/harvest.py
Pydantic schemas for harvest models.
"""

from decimal import Decimal

from pydantic import BaseModel

from app.schemas.base import AuditModelBase


class HarvestBase(BaseModel):
    """Base schema for harvests."""

    farm_id: int
    crop_id: int
    quality_grade_id: int
    weight_kg: Decimal


class HarvestCreate(HarvestBase):
    """Schema for creating a harvest."""

    pass


class HarvestUpdate(BaseModel):
    """Schema for updating a harvest."""

    farm_id: int | None = None
    crop_id: int | None = None
    quality_grade_id: int | None = None
    weight_kg: Decimal | None = None


class HarvestResponse(AuditModelBase, HarvestBase):
    """Schema for harvest response."""

    pass
