from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import FarmStatus
from app.schemas.common import TimestampResponse


class FarmBase(BaseModel):
    """Base schema describing a farm."""

    infrastructure_type_id: int
    growing_system_type_id: int
    name: str = Field(max_length=255)
    city: str | None = Field(default=None, max_length=255)
    size_m2: Decimal | None = Field(default=None, gt=0)
    status: FarmStatus = FarmStatus.ACTIVE
    growing_beds_count: int | None = Field(default=None, ge=0)


class FarmCreate(FarmBase):
    """Schema used for farm creation."""

    pass


class FarmUpdate(BaseModel):
    """Schema used for partial farm updates."""

    infrastructure_type_id: int | None = None
    growing_system_type_id: int | None = None
    name: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=255)
    size_m2: Decimal | None = None
    status: FarmStatus | None = None
    growing_beds_count: int | None = None


class FarmResponse(FarmBase, TimestampResponse):
    """Schema returned when retrieving farm information."""

    pass
