from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.farms.farm_status import FarmStatus
from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class FarmBase(BaseModel):
    """
    Shared fields for Farm entity.
    """

    infrastructure_type_id: int
    growing_system_type_id: int

    name: str = Field(default=None, max_length=255)
    status: FarmStatus = FarmStatus.ACTIVE
    city: str | None = Field(default=None, max_length=255)
    size_m2: Decimal | None = Field(default=None, gt=0)
    growing_beds_count: int | None = Field(default=None, ge=0)


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class FarmCreate(FarmBase):
    """
    Schema used for creating Farm.
    """

    pass


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class FarmUpdate(BaseModel):
    """
    Schema used for updating Farm.
    """

    name: str = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=255)
    size_m2: Decimal | None = Field(default=None, gt=0)
    status: FarmStatus | None = None
    growing_beds_count: int | None = Field(default=None, ge=0)

    infrastructure_type_id: int | None = None
    growing_system_type_id: int | None = None


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class FarmResponse(FarmBase, AuditSchema):
    """
    API response schema for Farm entity.
    """

    id: int
    status: FarmStatus

    model_config = ConfigDict(from_attributes=True)
