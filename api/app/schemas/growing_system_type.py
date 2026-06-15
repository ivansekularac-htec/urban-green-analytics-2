from pydantic import BaseModel, ConfigDict, Field


class GrowingSystemTypeBase(BaseModel):
    """Base schema for growing system type data."""

    name: str = Field(max_length=100)
    description: str | None = Field(max_length=500)


class GrowingSystemTypeCreate(GrowingSystemTypeBase):
    """Schema for creating a growing system type."""

    pass


class GrowingSystemTypeUpdate(BaseModel):
    """Schema for updating growing system type data."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class GrowingSystemTypeResponse(GrowingSystemTypeBase):
    """Schema for returning growing system type data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
