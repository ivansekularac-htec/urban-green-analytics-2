from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class InfrastructureTypeBase(BaseModel):
    """
    Shared fields for InfrastructureType.
    """

    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class InfrastructureTypeCreate(InfrastructureTypeBase):
    """
    Schema used for creating InfrastructureType.
    """

    pass


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class InfrastructureTypeUpdate(BaseModel):
    """
    Schema used for updating InfrastructureType.
    """

    name: str = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class InfrastructureTypeResponse(InfrastructureTypeBase, AuditSchema):
    """
    API response schema for InfrastructureType.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
