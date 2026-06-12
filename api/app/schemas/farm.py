"""
schemas/farm.py
Pydantic schemas for farm models.
"""

from decimal import Decimal

from pydantic import BaseModel, Field

from app.models import FarmStatus
from app.schemas.base import AuditModelBase


class FarmBase(BaseModel):
    """Base schema for farms."""

    infrastructure_type_id: int
    growing_system_type_id: int
    name: str = Field(..., max_length=255)
    city: str | None = Field(None, max_length=255)
    size_m2: Decimal | None = None
    status: FarmStatus = FarmStatus.ACTIVE
    growing_beds_count: int | None = None


class FarmCreate(FarmBase):
    """Schema for creating a farm."""

    pass


class FarmUpdate(BaseModel):
    """Schema for updating a farm."""

    infrastructure_type_id: int | None = None
    growing_system_type_id: int | None = None
    name: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=255)
    size_m2: Decimal | None = None
    status: FarmStatus | None = None
    growing_beds_count: int | None = None


class FarmResponse(AuditModelBase, FarmBase):
    """Schema for farm response."""

    pass
