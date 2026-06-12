from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import FarmStatus


class FarmBase(BaseModel):
    """Base schema for farm data."""

    infrastructure_type_id: int
    growing_system_type_id: int
    name: str
    city: str | None = None
    size_m2: Decimal | None = None
    status: FarmStatus = FarmStatus.ACTIVE
    growing_beds_count: int | None = None


class FarmCreate(FarmBase):
    """Schema for creating a farm."""

    pass


class FarmResponse(FarmBase):
    """Schema for returning farm data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
