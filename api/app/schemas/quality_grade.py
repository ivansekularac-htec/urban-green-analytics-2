"""
schemas/quality_grade.py
Pydantic schemas for quality grade models.
"""

from pydantic import BaseModel, Field

from app.schemas.base import AuditModelBase


class QualityGradeBase(BaseModel):
    """Base schema for quality grades."""

    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=500)


class QualityGradeCreate(QualityGradeBase):
    """Schema for creating a quality grade."""

    pass


class QualityGradeUpdate(BaseModel):
    """Schema for updating a quality grade."""

    code: str | None = Field(None, max_length=50)
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)


class QualityGradeResponse(AuditModelBase, QualityGradeBase):
    """Schema for quality grade response."""

    pass
