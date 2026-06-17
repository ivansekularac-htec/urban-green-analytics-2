from typing import Annotated

from fastapi import Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db

DBSession = Annotated[
    Session,
    Depends(get_db),
]


class PaginationParams(BaseModel):
    skip: int
    limit: int


def get_pagination(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of records to skip",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of records to return",
    ),
) -> PaginationParams:
    return PaginationParams(
        skip=skip,
        limit=limit,
    )


PaginationDep = Annotated[
    PaginationParams,
    Depends(get_pagination),
]
