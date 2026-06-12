from pydantic import BaseModel, Field

from app.schemas.base import AuditModelBase


class FarmInfrastructureTypeBase(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class FarmInfrastructureTypeCreate(FarmInfrastructureTypeBase):
    pass


class FarmInfrastructureTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class FarmInfrastructureTypeResponse(
    AuditModelBase,
    FarmInfrastructureTypeBase,
):
    pass
