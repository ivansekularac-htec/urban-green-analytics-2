from decimal import Decimal

from api.app.schemas.audit import AuditSchema
from pydantic import BaseModel

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class HarvestBase(BaseModel):
    """
    Shared fields for Harvest entity.
    """

    farm_id: int
    crop_id: int
    quality_grade_id: int
    weight_kg: Decimal


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class HarvestCreate(HarvestBase):
    """
    Schema used for creating Harvest record.
    """


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class HarvestUpdate(BaseModel):
    """
    Schema used for updating Harvest record.
    """

    weight_kg: Decimal | None = None
    quality_grade_id: int | None = None


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class HarvestResponse(HarvestBase, AuditSchema):
    """
    API response schema for Harvest entity.
    """

    id: int

    class Config:
        from_attributes = True
