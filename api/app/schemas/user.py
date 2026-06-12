from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    email: str
    full_name: str
    is_active: bool


class UserCreate(UserBase):
    password_hash: str


class UserResponse(UserBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
