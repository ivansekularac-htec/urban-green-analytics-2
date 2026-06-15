from pydantic import BaseModel, ConfigDict, Field


class CropCategoryBase(BaseModel):
    """Base schema for crop category data."""

    name: str = Field(max_length=100)
    description: str | None = Field(max_length=500)


class CropCategoryCreate(CropCategoryBase):
    """Schema for creating a crop category."""

    pass


class CropCategoryUpdate(BaseModel):
    """Schema for updating crop category data."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class CropCategoryResponse(CropCategoryBase):
    """Schema for returning crop category data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
