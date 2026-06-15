from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FarmStatus


class FarmBase(BaseModel):
    """Base schema for farm data."""

    infrastructure_type_id: int
    growing_system_type_id: int
    name: str = Field(max_length=255)
    city: str | None = Field(max_length=255)
    size_m2: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=3,
    )
    status: FarmStatus = FarmStatus.ACTIVE
    growing_beds_count: int | None = None


class FarmCreate(FarmBase):
    """Schema for creating a farm."""

    pass


class FarmUpdate(BaseModel):
    """Schema for updating farm data."""

    infrastructure_type_id: int | None = None
    growing_system_type_id: int | None = None
    name: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=255)
    size_m2: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=3,
    )
    status: FarmStatus | None = None
    growing_beds_count: int | None = None


class FarmResponse(FarmBase):
    """Schema for returning farm data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
