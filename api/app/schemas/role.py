"""
schemas/role.py
Pydantic schemas for role models.
"""

from pydantic import BaseModel, Field

from app.schemas.base import AuditModelBase


class RoleBase(BaseModel):
    """Base schema for roles."""

    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=500)


class RoleCreate(RoleBase):
    """Schema for creating a role."""

    pass


class RoleUpdate(BaseModel):
    """Schema for updating a role."""

    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)


class RoleResponse(AuditModelBase, RoleBase):
    """Schema for role response."""

    pass
