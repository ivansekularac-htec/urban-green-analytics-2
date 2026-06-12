from pydantic import BaseModel, ConfigDict


class CropCategoryBase(BaseModel):
    """Base schema for crop category data."""

    name: str
    description: str | None = None


class CropCategoryCreate(CropCategoryBase):
    """Schema for creating a crop category."""

    pass


class CropCategoryResponse(CropCategoryBase):
    """Schema for returning crop category data from the API."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
