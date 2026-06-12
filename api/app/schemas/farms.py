from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import FarmStatus
from app.schemas.base import AuditModelBase


class FarmBase(BaseModel):
    infrastructure_type_id: int
    growing_system_type_id: int
    name: str = Field(max_length=255)
    city: str | None = Field(default=None, max_length=255)
    size_m2: Decimal | None = None
    status: FarmStatus = FarmStatus.ACTIVE
    growing_beds_count: int | None = None


class FarmCreate(FarmBase):
    pass


class FarmUpdate(BaseModel):
    infrastructure_type_id: int | None = None
    growing_system_type_id: int | None = None
    name: str | None = None
    city: str | None = None
    size_m2: Decimal | None = None
    status: FarmStatus | None = None
    growing_beds_count: int | None = None


class FarmResponse(
    AuditModelBase,
    FarmBase,
):
    pass
