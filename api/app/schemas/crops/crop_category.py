from pydantic import BaseModel

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class CropCategoryBase(BaseModel):
    """
    Shared fields for CropCategory.
    """

    name: str
    description: str | None = None


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

    name: str | None = None
    description: str | None = None


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class CropCategoryResponse(CropCategoryBase, AuditSchema):
    """
    API response schema for CropCategory.
    """

    id: int

    class Config:
        from_attributes = True
