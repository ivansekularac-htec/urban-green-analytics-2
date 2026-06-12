from pydantic import BaseModel, ConfigDict


class FarmCropBase(BaseModel):
    farm_id: int | None = None
    crop_id: int | None = None
    started_at: int | None = None
    ended_at: int | None = None


class FarmCropCreate(FarmCropBase):
    pass


class FarmCropResponse(FarmCropBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class FarmCropUpdate(BaseModel):
    farm_id: int | None = None
    crop_id: int | None = None
    started_at: int | None = None
    ended_at: int | None = None
