from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import FarmStatus
from app.schemas.base import AuditModelBase


class FarmBase(BaseModel):
    infrastructure_type_id: int
    growing_system_type_id: int
    name: str
    city: str | None = None
    size_m2: Decimal | None = None
    status: FarmStatus = FarmStatus.ACTIVE
    growing_beds_count: int | None = None


class FarmCreate(FarmBase):
    pass


class FarmResponse(
    AuditModelBase,
    FarmBase,
):
    pass