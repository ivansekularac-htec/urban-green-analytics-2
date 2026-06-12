from pydantic import BaseModel, Field

from app.schemas.common import TimestampResponse


class CropCategoryBase(BaseModel):
    """Base schema for crop category data."""

    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class CropCategoryCreate(CropCategoryBase):
    """Schema used for crop category creation."""

    pass


class CropCategoryUpdate(BaseModel):
    """Schema used for partial crop category updates."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class CropCategoryResponse(CropCategoryBase, TimestampResponse):
    """Schema returned when retrieving crop category information."""

    pass
