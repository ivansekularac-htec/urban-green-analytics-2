from pydantic import BaseModel, ConfigDict


class UserRoleBase(BaseModel):
    """Base schema for user role assignment data."""

    user_id: int
    role_id: int
    farm_id: int | None = None


class UserRoleCreate(UserRoleBase):
    """Schema for creating a user role assignment."""

    pass


class UserRoleResponse(UserRoleBase):
    """Schema for returning user role assignment data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
