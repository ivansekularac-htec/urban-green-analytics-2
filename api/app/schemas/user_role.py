from pydantic import BaseModel

from app.schemas.common import TimestampResponse


class UserRoleBase(BaseModel):
    """Base schema for user role data."""

    user_id: int
    role_id: int
    farm_id: int | None = None


class UserRoleCreate(UserRoleBase):
    """Schema used for user role creation."""

    pass


class UserRoleUpdate(BaseModel):
    """Schema used for partial user role updates."""

    user_id: int | None = None
    role_id: int | None = None
    farm_id: int | None = None


class UserRoleResponse(UserRoleBase, TimestampResponse):
    """Schema returned when retrieving user role information."""

    pass
