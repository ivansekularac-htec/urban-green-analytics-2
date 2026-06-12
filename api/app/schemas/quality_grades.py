from pydantic import BaseModel

from app.schemas.base import AuditModelBase


class QualityGradeBase(BaseModel):
    code: str
    name: str
    description: str | None = None


class QualityGradeCreate(QualityGradeBase):
    pass


class QualityGradeResponse(AuditModelBase, QualityGradeBase):
    pass