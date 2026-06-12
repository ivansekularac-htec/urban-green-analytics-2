from decimal import Decimal

from pydantic import BaseModel

from app.schemas.base import BaseResponse


class HarvestBase(BaseModel):
    farm_id: int
    crop_id: int
    quality_grade_id: int

    weight_kg: Decimal


class HarvestCreate(HarvestBase):
    pass


class HarvestUpdate(BaseModel):
    farm_id: int | None = None
    crop_id: int | None = None
    quality_grade_id: int | None = None
    weight_kg: Decimal | None = None


class HarvestResponse(HarvestBase, BaseResponse):
    pass
