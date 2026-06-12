from pydantic import BaseModel, ConfigDict, Field


class CropCategoryBase(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class CropCategoryCreate(CropCategoryBase):
    pass


class CropCategoryResponse(CropCategoryBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class CropCategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
