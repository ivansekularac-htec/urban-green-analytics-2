from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audit import AuditSchema

# ------------------------------------------------------
# Base
# ------------------------------------------------------


class QualityGradeBase(BaseModel):
    """
    Shared fields for QualityGrade entity.
    """

    code: str = Field(default=None, max_length=50)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


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

    code: str = Field(default=None, max_length=50)
    name: str = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)


# ------------------------------------------------------
# Response
# ------------------------------------------------------


class QualityGradeResponse(QualityGradeBase, AuditSchema):
    """
    API response schema for QualityGrade.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
