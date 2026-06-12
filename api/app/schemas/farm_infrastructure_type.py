from pydantic import BaseModel, ConfigDict


class FarmInfrastructureTypeBase(BaseModel):
    name: str
    description: str | None = None


class FarmInfrastructureTypeCreate(FarmInfrastructureTypeBase):
    pass


class FarmInfrastructureTypeResponse(FarmInfrastructureTypeBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
