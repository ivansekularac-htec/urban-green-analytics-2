from pydantic import BaseModel, ConfigDict


class FarmCropBase(BaseModel):
    """Base schema for farm crop assignment data."""

    farm_id: int
    crop_id: int
    started_at: int
    ended_at: int | None = None


class FarmCropCreate(FarmCropBase):
    """Schema for creating a farm crop assignment."""

    pass


class FarmCropUpdate(BaseModel):
    """Schema for updating farm crop assignment data."""

    farm_id: int | None = None
    crop_id: int | None = None
    started_at: int | None = None
    ended_at: int | None = None


class FarmCropResponse(FarmCropBase):
    """Schema for returning farm crop assignment data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
