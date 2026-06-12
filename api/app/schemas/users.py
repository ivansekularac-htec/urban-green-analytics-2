from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import AuditModelBase


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(max_length=255)
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None
    password: str | None = None


class UserResponse(
    AuditModelBase,
    UserBase,
):
    pass
