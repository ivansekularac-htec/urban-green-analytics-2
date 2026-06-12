from pydantic import BaseModel

from app.schemas.base import AuditModelBase


class UserRoleBase(BaseModel):
    user_id: int
    role_id: int
    farm_id: int | None = None


class UserRoleCreate(UserRoleBase):
    pass


class UserRoleResponse(
    AuditModelBase,
    UserRoleBase,
):
    pass