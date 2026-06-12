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


class FarmCropResponse(FarmCropBase):
    """Schema for returning farm crop assignment data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
