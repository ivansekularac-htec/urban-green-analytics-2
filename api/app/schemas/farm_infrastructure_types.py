from pydantic import BaseModel

from app.schemas.base import AuditModelBase


class FarmInfrastructureTypeBase(BaseModel):
    name: str
    description: str | None = None


class FarmInfrastructureTypeCreate(FarmInfrastructureTypeBase):
    pass


class FarmInfrastructureTypeResponse(
    AuditModelBase,
    FarmInfrastructureTypeBase,
):
    pass