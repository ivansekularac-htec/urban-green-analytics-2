from pydantic import BaseModel, Field

from app.schemas.common import TimestampResponse


class RoleBase(BaseModel):
    """Base schema for role data."""

    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class RoleCreate(RoleBase):
    """Schema used for role creation."""

    pass


class RoleUpdate(BaseModel):
    """Schema used for partial role updates."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class RoleResponse(RoleBase, TimestampResponse):
    """Schema returned when retrieving role information."""

    pass
