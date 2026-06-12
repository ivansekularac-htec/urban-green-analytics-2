from pydantic import BaseModel, ConfigDict


class CropCategoryBase(BaseModel):
    name: str
    description: str | None = None


class CropCategoryCreate(CropCategoryBase):
    pass


class CropCategoryResponse(CropCategoryBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
