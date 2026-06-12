"""
schemas/crop.py
Pydantic schemas for crop and crop category models.
"""

from pydantic import BaseModel, Field

from app.schemas.base import AuditModelBase


class CropCategoryBase(BaseModel):
    """Base schema for crop categories."""

    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=500)


class CropCategoryCreate(CropCategoryBase):
    """Schema for creating a crop category."""

    pass


class CropCategoryUpdate(BaseModel):
    """Schema for updating a crop category."""

    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)


class CropCategoryResponse(AuditModelBase, CropCategoryBase):
    """Schema for crop category response."""

    pass


class CropBase(BaseModel):
    """Base schema for crops."""

    category_id: int
    name: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=500)


class CropCreate(CropBase):
    """Schema for creating a crop."""

    pass


class CropUpdate(BaseModel):
    """Schema for updating a crop."""

    category_id: int | None = None
    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=500)


class CropResponse(AuditModelBase, CropBase):
    """Schema for crop response."""

    pass
