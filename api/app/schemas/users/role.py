from api.app.schemas.audit import AuditSchema
from pydantic import BaseModel

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class RoleBase(BaseModel):
    """
    Shared fields for Role entity.
    """

    name: str
    description: str | None = None


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

    name: str | None = None
    description: str | None = None


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class RoleResponse(RoleBase, AuditSchema):
    """
    API response schema for Role entity.
    """

    id: int

    class Config:
        from_attributes = True
