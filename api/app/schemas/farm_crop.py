from pydantic import BaseModel

from app.schemas.common import TimestampResponse


class FarmCropBase(BaseModel):
    """Base schema representing crop cultivation on a farm."""

    farm_id: int
    crop_id: int
    started_at: int
    ended_at: int | None = None


class FarmCropCreate(FarmCropBase):
    """Schema used for creating a farm-crop association."""

    pass


class FarmCropUpdate(BaseModel):
    """Schema used for updating a farm-crop association."""

    farm_id: int | None = None
    crop_id: int | None = None
    started_at: int | None = None
    ended_at: int | None = None


class FarmCropResponse(FarmCropBase, TimestampResponse):
    """Schema returned when retrieving farm-crop records."""

    pass
