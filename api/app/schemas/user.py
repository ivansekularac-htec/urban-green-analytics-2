"""
schemas/user.py
Pydantic schemas for user and user role models.
"""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import AuditModelBase


class UserBase(BaseModel):
    """Base schema for users."""

    email: EmailStr
    full_name: str = Field(..., max_length=255)
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., max_length=255)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    full_name: str | None = Field(None, max_length=255)
    is_active: bool | None = None
    password: str | None = Field(None, max_length=255)


class UserResponse(AuditModelBase, UserBase):
    """Schema for user response."""

    pass


class UserRoleBase(BaseModel):
    """Base schema for user roles."""

    user_id: int
    role_id: int
    farm_id: int | None = None


class UserRoleCreate(UserRoleBase):
    """Schema for creating a user role."""

    pass


class UserRoleUpdate(BaseModel):
    """Schema for updating a user role."""

    user_id: int | None = None
    role_id: int | None = None
    farm_id: int | None = None


class UserRoleResponse(AuditModelBase, UserRoleBase):
    """Schema for user role response."""

    pass
