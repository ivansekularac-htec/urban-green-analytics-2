from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """Base schema for user data."""

    email: EmailStr
    full_name: str
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user."""

    password_hash: str


class UserResponse(UserBase):
    """Schema for returning user data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
