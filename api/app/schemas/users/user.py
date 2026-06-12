from pydantic import BaseModel, ConfigDict, EmailStr

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class UserBase(BaseModel):
    """
    Shared fields for User entity.
    """

    email: EmailStr
    full_name: str
    is_active: bool = True


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class UserCreate(UserBase):
    """
    Schema used for creating User.
    """

    password_hash: str


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class UserUpdate(BaseModel):
    """
    Schema used for updating User.
    """

    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None


# ------------------------------------------------------
# Password Update
# ------------------------------------------------------


class UserPasswordUpdate(BaseModel):
    """
    Schema used for changing user password.
    """

    password_hash: str


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class UserResponse(UserBase, AuditSchema):
    """
    API response schema for User.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
