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


class HarvestResponse(HarvestBase, BaseResponse):
    pass
