from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class RoleBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class RoleResponse(RoleBase, BaseResponse):
    pass
