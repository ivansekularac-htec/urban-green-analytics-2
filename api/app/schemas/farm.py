from decimal import Decimal

from pydantic import BaseModel, Field

from app.enums import FarmStatus
from app.schemas.base import BaseResponse


class FarmBase(BaseModel):
    infrastructure_type_id: int
    growing_system_type_id: int

    name: str = Field(
        min_length=1,
        max_length=255,
    )
    city: str | None = Field(
        min_length=1,
        max_length=255,
    )

    size_m2: Decimal | None = None
    status: FarmStatus = FarmStatus.ACTIVE
    growing_beds_count: int | None = None


class FarmCreate(FarmBase):
    pass


class FarmResponse(FarmBase, BaseResponse):
    pass
