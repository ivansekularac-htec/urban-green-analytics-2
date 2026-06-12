from pydantic import BaseModel, Field

from app.schemas.base import AuditModelBase


class CropCategoryBase(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class CropCategoryCreate(CropCategoryBase):
    pass


class CropCategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CropCategoryResponse(
    AuditModelBase,
    CropCategoryBase,
):
    pass
