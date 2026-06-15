from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class CropCategoryBase(BaseModel):
    """
    Shared fields for CropCategory.
    """

    name: str = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class CropCategoryCreate(CropCategoryBase):
    """
    Schema used for creating CropCategory.
    """

    pass


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class CropCategoryUpdate(BaseModel):
    """
    Schema used for updating CropCategory.
    """

    name: str = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class CropCategoryResponse(CropCategoryBase, AuditSchema):
    """
    API response schema for CropCategory.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
