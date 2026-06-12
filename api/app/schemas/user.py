from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import BaseResponse


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(
        min_length=1,
        max_length=255,
    )
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=255,
    )


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    is_active: bool | None = None


class UserResponse(UserBase, BaseResponse):
    pass
