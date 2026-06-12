from pydantic import BaseModel, ConfigDict


class QualityGradeBase(BaseModel):
    code: str
    name: str
    description: str | None = None


class QualityGradeCreate(QualityGradeBase):
    pass


class QualityGradeResponse(QualityGradeBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
