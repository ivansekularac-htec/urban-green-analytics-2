from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class FarmInfrastructureTypeBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class FarmInfrastructureTypeCreate(FarmInfrastructureTypeBase):
    pass


class FarmInfrastructureTypeResponse(FarmInfrastructureTypeBase, BaseResponse):
    pass
