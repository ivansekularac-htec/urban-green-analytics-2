from api.app.schemas.audit import AuditSchema
from pydantic import BaseModel

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class UserRoleBase(BaseModel):
    """
    Shared fields for UserRole entity.
    """

    user_id: int
    role_id: int
    farm_id: int | None = None


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class UserRoleCreate(UserRoleBase):
    """
    Schema used for creating UserRole.
    """

    pass


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class UserRoleUpdate(BaseModel):
    """
    Schema used for updating UserRole.
    """

    user_id: int | None = None
    role_id: int | None = None
    farm_id: int | None = None


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class UserRoleResponse(UserRoleBase, AuditSchema):
    """
    API response schema for UserRole.
    """

    id: int

    class Config:
        from_attributes = True
