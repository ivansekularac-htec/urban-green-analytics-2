from pydantic import BaseModel

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class QualityGradeBase(BaseModel):
    """
    Shared fields for QualityGrade entity.
    """

    code: str
    name: str
    description: str | None = None


# ------------------------------------------------------
# Create
# ------------------------------------------------------


class QualityGradeCreate(QualityGradeBase):
    """
    Schema used for creating QualityGrade.
    """

    pass


# ------------------------------------------------------
# Update
# ------------------------------------------------------


class QualityGradeUpdate(BaseModel):
    """
    Schema used for updating QualityGrade.
    """

    code: str | None = None
    name: str | None = None
    description: str | None = None


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class QualityGradeResponse(QualityGradeBase, AuditSchema):
    """
    API response schema for QualityGrade.
    """

    id: int

    class Config:
        from_attributes = True
