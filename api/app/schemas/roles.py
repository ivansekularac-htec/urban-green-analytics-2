from pydantic import BaseModel, Field

from app.schemas.base import AuditModelBase


class RoleBase(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class RoleResponse(AuditModelBase, RoleBase):
    pass
