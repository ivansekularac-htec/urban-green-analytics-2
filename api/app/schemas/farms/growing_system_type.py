from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class GrowingSystemTypeBase(BaseModel):
    """
    Shared fields for GrowingSystemType.
    """

    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


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

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class GrowingSystemTypeResponse(GrowingSystemTypeBase, AuditSchema):
    """
    API response schema for GrowingSystemType.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
