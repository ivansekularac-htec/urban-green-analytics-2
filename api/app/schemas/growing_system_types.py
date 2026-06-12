from pydantic import BaseModel

from app.schemas.base import AuditModelBase


class GrowingSystemTypeBase(BaseModel):
    name: str
    description: str | None = None


class GrowingSystemTypeCreate(GrowingSystemTypeBase):
    pass


class GrowingSystemTypeResponse(
    AuditModelBase,
    GrowingSystemTypeBase,
):
    pass