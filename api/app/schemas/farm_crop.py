from pydantic import BaseModel

from app.schemas.base import BaseResponse


class FarmCropBase(BaseModel):
    farm_id: int
    crop_id: int
    started_at: int
    ended_at: int | None = None


class FarmCropCreate(FarmCropBase):
    pass


class FarmCropResponse(FarmCropBase, BaseResponse):
    pass
