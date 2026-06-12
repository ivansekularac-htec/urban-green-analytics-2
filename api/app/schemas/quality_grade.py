from pydantic import BaseModel, ConfigDict, Field


class QualityGradeBase(BaseModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class QualityGradeCreate(QualityGradeBase):
    pass


class QualityGradeResponse(QualityGradeBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class QualityGradeUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
