from pydantic import BaseModel, ConfigDict


class FarmCropBase(BaseModel):
    farm_id: int
    crop_id: int
    started_at: int
    ended_at: int | None = None


class FarmCropCreate(FarmCropBase):
    pass


class FarmCropResponse(FarmCropBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
