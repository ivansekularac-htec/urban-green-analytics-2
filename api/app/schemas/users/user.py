from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class UserBase(BaseModel):
    """
    Shared fields for User entity.
    """

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = True


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class UserCreate(UserBase):
    """
    Schema used for creating User.
    """

    password: str = Field(min_length=8, max_length=255)


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class UserUpdate(BaseModel):
    """
    Schema used for updating User.
    """

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


# ------------------------------------------------------
# Password Update
# ------------------------------------------------------


class UserPasswordUpdate(BaseModel):
    """
    Schema used for changing user password.
    """

    password: str = Field(min_length=8, max_length=255)


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class UserResponse(UserBase, AuditSchema):
    """
    API response schema for User.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
