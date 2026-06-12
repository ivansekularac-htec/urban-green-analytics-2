from api.app.schemas.audit import AuditSchema
from pydantic import BaseModel

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class GrowingSystemTypeBase(BaseModel):
    """
    Shared fields for GrowingSystemType.
    """

    name: str
    description: str | None = None


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class GrowingSystemTypeCreate(GrowingSystemTypeBase):
    """
    Schema used for creating GrowingSystemType.
    """

    pass


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class GrowingSystemTypeUpdate(BaseModel):
    """
    Schema used for updating GrowingSystemType.
    """

    name: str | None = None
    description: str | None = None


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class GrowingSystemTypeResponse(GrowingSystemTypeBase, AuditSchema):
    """
    API response schema for GrowingSystemType.
    """

    id: int

    class Config:
        from_attributes = True
