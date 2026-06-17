from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audit import AuditSchema

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
    weight_kg: Decimal = Field(gt=0)


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class HarvestCreate(HarvestBase):
    """
    Schema used for creating Harvest record.
    """

    pass


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class HarvestUpdate(BaseModel):
    """
    Schema used for updating Harvest record.
    """

    weight_kg: Decimal | None = Field(gt=0, default=None)
    quality_grade_id: int | None = None


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class HarvestResponse(HarvestBase, AuditSchema):
    """
    API response schema for Harvest entity.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
