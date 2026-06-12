from pydantic import BaseModel, Field

from app.schemas.common import TimestampResponse


class CropBase(BaseModel):
    """Base schema for crop data."""

    category_id: int
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=500)


class CropCreate(CropBase):
    """Schema used for crop creation."""

    pass


class CropUpdate(BaseModel):
    """Schema used for partial crop updates."""

    category_id: int | None = None
    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)


class CropResponse(CropBase, TimestampResponse):
    """Schema returned when retrieving crop information."""

    pass
