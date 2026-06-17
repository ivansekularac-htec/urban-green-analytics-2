from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class CropBase(BaseModel):
    """
    Shared fields for Crop entity.
    """

    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


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


class CropResponse(CropBase, AuditSchema):
    """
    API response schema for Crop.
    """

    id: int
    category_id: int

    model_config = ConfigDict(from_attributes=True)
