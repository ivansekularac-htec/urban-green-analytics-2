from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(max_length=255)
    is_active: bool


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None
    password: str | None = None
