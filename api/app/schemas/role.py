from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    name: str = Field(max_length=100)
    unit: str = Field(max_length=50)
    description: str | None = Field(default=None, max_length=500)


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class SensorTypeUpdate(BaseModel):
    name: str | None = None
    unit: str | None = None
    description: str | None = None
    optimal_min: Decimal | None = None
    optimal_max: Decimal | None = None
