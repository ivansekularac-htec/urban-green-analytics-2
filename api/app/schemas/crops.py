from pydantic import BaseModel

from app.schemas.base import AuditModelBase


class CropBase(BaseModel):
    category_id: int
    name: str
    description: str | None = None


class CropCreate(CropBase):
    pass


class CropResponse(
    AuditModelBase,
    CropBase,
):
    pass