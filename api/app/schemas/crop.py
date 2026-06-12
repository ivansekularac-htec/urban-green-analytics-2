from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class CropBase(BaseModel):
    category_id: int
    name: str = Field(
        min_length=1,
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class CropCreate(CropBase):
    pass


class CropUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)


class CropResponse(CropBase, BaseResponse):
    pass
