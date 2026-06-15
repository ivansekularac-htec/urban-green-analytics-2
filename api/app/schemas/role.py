from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    """Base schema for role data."""

    name: str = Field(max_length=100)
    description: str | None = Field(max_length=500)


class RoleCreate(RoleBase):
    """Schema for creating a role."""

    pass


class RoleUpdate(BaseModel):
    """Schema for updating role data."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class RoleResponse(RoleBase):
    """Schema for returning role data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
