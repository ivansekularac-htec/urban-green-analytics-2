from pydantic import BaseModel

from app.schemas.base import AuditModelBase


class FarmCropBase(BaseModel):
    farm_id: int
    crop_id: int
    started_at: int
    ended_at: int | None = None


class FarmCropCreate(FarmCropBase):
    pass


class FarmCropUpdate(BaseModel):
    farm_id: int | None = None
    crop_id: int | None = None
    started_at: int | None = None
    ended_at: int | None = None


class FarmCropResponse(
    AuditModelBase,
    FarmCropBase,
):
    pass
