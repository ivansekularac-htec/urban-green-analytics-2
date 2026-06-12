from pydantic import BaseModel, ConfigDict

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class FarmCropBase(BaseModel):
    """
    Shared fields for FarmCrop entity.
    """

    started_at: int
    ended_at: int | None = None


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class FarmCropCreate(FarmCropBase):
    """
    Schema used for creating FarmCrop record.
    """

    farm_id: int
    crop_id: int


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class FarmCropUpdate(BaseModel):
    """
    Schema used for updating FarmCrop record.
    """

    started_at: int | None = None
    ended_at: int | None = None


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class FarmCropResponse(FarmCropBase, AuditSchema):
    """
    API response schema for FarmCrop.
    """

    id: int
    farm_id: int
    crop_id: int

    model_config = ConfigDict(from_attributes=True)
