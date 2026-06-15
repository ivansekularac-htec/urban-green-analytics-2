from pydantic import BaseModel, ConfigDict, Field


class FarmInfrastructureTypeBase(BaseModel):
    """Base schema for farm infrastructure type data."""

    name: str = Field(max_length=100)
    description: str | None = Field(max_length=500)


class FarmInfrastructureTypeCreate(FarmInfrastructureTypeBase):
    """Schema for creating a farm infrastructure type."""

    pass


class FarmInfrastructureTypeUpdate(BaseModel):
    """Schema for updating farm infrastructure type data."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class FarmInfrastructureTypeResponse(FarmInfrastructureTypeBase):
    """Schema for returning farm infrastructure type data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
