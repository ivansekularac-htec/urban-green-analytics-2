from pydantic import BaseModel, ConfigDict


class GrowingSystemTypeBase(BaseModel):
    name: str
    description: str | None = None


class GrowingSystemTypeCreate(GrowingSystemTypeBase):
    pass


class GrowingSystemTypeResponse(GrowingSystemTypeBase):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
