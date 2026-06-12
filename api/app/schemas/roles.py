from pydantic import BaseModel

from app.schemas.base import AuditModelBase


class RoleBase(BaseModel):
    name: str
    description: str | None = None


class RoleCreate(RoleBase):
    pass


class RoleResponse(AuditModelBase, RoleBase):
    pass