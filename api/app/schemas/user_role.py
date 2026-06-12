from pydantic import BaseModel

from app.schemas.base import BaseResponse


class UserRoleBase(BaseModel):
    user_id: int
    role_id: int
    farm_id: int | None = None


class UserRoleCreate(UserRoleBase):
    pass


class UserRoleUpdate(BaseModel):
    user_id: int | None = None
    role_id: int | None = None
    farm_id: int | None = None


class UserRoleResponse(UserRoleBase, BaseResponse):
    pass
