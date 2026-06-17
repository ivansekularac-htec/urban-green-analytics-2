"""
Shared pagination dependencies.
"""

from typing import Annotated

from fastapi import Depends, Query
from pydantic import BaseModel

DEFAULT_PAGE_LIMIT = 100
MAX_PAGE_LIMIT = 200


class PaginationParams(BaseModel):
    """
    Validated pagination query parameters.
    """

    skip: int
    limit: int


def get_pagination_params(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)] = DEFAULT_PAGE_LIMIT,
) -> PaginationParams:
    """
    Return validated pagination query parameters.
    """
    return PaginationParams(skip=skip, limit=limit)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]
