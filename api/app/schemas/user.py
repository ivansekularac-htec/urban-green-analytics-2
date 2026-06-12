from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import TimestampResponse


class UserBase(BaseModel):
    """Base schema for user data."""

    email: EmailStr
    full_name: str = Field(max_length=255)
    is_active: bool = True


class UserCreate(UserBase):
    """Schema used for user creation."""

    password: str = Field(min_length=8, max_length=255)


class UserUpdate(BaseModel):
    """Schema used for partial user updates."""

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    password: str | None = None


class UserResponse(UserBase, TimestampResponse):
    """Schema returned when retrieving user information."""

    pass
