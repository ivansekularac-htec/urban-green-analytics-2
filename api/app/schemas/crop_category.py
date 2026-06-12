from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class CropCategoryBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class CropCategoryCreate(CropCategoryBase):
    pass


class CropCategoryUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class CropCategoryResponse(CropCategoryBase, BaseResponse):
    pass
