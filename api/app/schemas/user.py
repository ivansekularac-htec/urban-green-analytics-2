from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base schema for user data."""

    email: EmailStr = Field(max_length=255)
    full_name: str = Field(max_length=255)
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Schema for updating user data."""

    email: EmailStr | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class UserResponse(UserBase):
    """Schema for returning user data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
