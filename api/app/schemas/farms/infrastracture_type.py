from pydantic import BaseModel

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class InfrastructureTypeBase(BaseModel):
    """
    Shared fields for InfrastructureType.
    """

    name: str
    description: str | None = None


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

    name: str | None = None
    description: str | None = None


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class InfrastructureTypeResponse(InfrastructureTypeBase, AuditSchema):
    """
    API response schema for InfrastructureType.
    """

    id: int

    class Config:
        from_attributes = True
