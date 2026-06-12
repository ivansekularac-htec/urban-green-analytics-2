from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class GrowingSystemTypeBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class GrowingSystemTypeCreate(GrowingSystemTypeBase):
    pass


class GrowingSystemTypeResponse(GrowingSystemTypeBase, BaseResponse):
    pass
