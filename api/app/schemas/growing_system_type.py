from pydantic import BaseModel, ConfigDict, Field


class GrowingSystemTypeBase(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class GrowingSystemTypeCreate(GrowingSystemTypeBase):
    pass


class GrowingSystemTypeResponse(GrowingSystemTypeBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class GrowingSystemTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
