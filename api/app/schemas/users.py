from pydantic import BaseModel

from app.schemas.base import AuditModelBase


class UserBase(BaseModel):
    email: str
    full_name: str
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserResponse(
    AuditModelBase,
    UserBase,
):
    pass