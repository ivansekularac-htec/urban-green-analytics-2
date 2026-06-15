from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class RoleBase(BaseModel):
    """
    Shared fields for Role entity.
    """

    name: str = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class RoleCreate(RoleBase):
    """
    Schema used for creating Role.
    """

    pass


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class RoleUpdate(BaseModel):
    """
    Schema used for updating Role.
    """

    name: str = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class RoleResponse(RoleBase, AuditSchema):
    """
    API response schema for Role entity.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
