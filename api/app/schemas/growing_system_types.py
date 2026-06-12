from pydantic import BaseModel, Field

from app.schemas.base import AuditModelBase


class GrowingSystemTypeBase(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class GrowingSystemTypeCreate(GrowingSystemTypeBase):
    pass


class GrowingSystemTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class GrowingSystemTypeResponse(
    AuditModelBase,
    GrowingSystemTypeBase,
):
    pass
