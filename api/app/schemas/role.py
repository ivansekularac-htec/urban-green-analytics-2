from pydantic import BaseModel, ConfigDict


class RoleBase(BaseModel):
    """Base schema for role data."""

    name: str
    description: str | None = None


class RoleCreate(RoleBase):
    """Schema for creating a role."""

    pass


class RoleResponse(RoleBase):
    """Schema for returning role data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
