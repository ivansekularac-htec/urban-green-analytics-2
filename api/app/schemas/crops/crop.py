from pydantic import BaseModel, ConfigDict

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class CropBase(BaseModel):
    """
    Shared fields for Crop entity.
    """

    name: str
    description: str | None = None


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class CropCreate(CropBase):
    """
    Schema used for creating Crop.
    """

    category_id: int


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class CropUpdate(BaseModel):
    """
    Schema used for updating Crop.
    """

    name: str | None = None
    description: str | None = None
    category_id: int | None = None


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class CropResponse(CropBase, AuditSchema):
    """
    API response schema for Crop.
    """

    id: int
    category_id: int

    model_config = ConfigDict(from_attributes=True)
