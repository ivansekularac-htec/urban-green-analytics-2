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
        default=None,
        min_length=1,
        max_length=255,
    )

    size_m2: Decimal | None = None
    status: FarmStatus = FarmStatus.ACTIVE
    growing_beds_count: int | None = None


class FarmCreate(FarmBase):
    pass


class FarmUpdate(BaseModel):
    infrastructure_type_id: int | None
    growing_system_type_id: int | None

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    city: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    size_m2: Decimal | None = None
    status: FarmStatus | None = None
    growing_beds_count: int | None = None


class FarmResponse(FarmBase, BaseResponse):
    pass
