"""
schemas/farm_crop.py
Pydantic schemas for farm-crop association models.
"""

from pydantic import BaseModel

from app.schemas.base import AuditModelBase


class FarmCropBase(BaseModel):
    """Base schema for farm crops."""

    farm_id: int
    crop_id: int
    started_at: int
    ended_at: int | None = None


class FarmCropCreate(FarmCropBase):
    """Schema for creating a farm crop."""

    pass


class FarmCropUpdate(BaseModel):
    """Schema for updating a farm crop."""

    farm_id: int | None = None
    crop_id: int | None = None
    started_at: int | None = None
    ended_at: int | None = None


class FarmCropResponse(AuditModelBase, FarmCropBase):
    """Schema for farm crop response."""

    pass
