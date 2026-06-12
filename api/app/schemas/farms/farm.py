from pydantic import BaseModel

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

    name: str
    city: str | None = None
    size_m2: float | None = None
    growing_beds_count: int | None = None


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

    name: str | None = None
    city: str | None = None
    size_m2: float | None = None
    status: FarmStatus | None = None
    growing_beds_count: int | None = None

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

    class Config:
        from_attributes = True
