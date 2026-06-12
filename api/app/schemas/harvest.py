from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class HarvestBase(BaseModel):
    farm_id: int
    crop_id: int
    quality_grade_id: int
    weight_kg: Decimal


class HarvestCreate(HarvestBase):
    pass


class HarvestResponse(HarvestBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
