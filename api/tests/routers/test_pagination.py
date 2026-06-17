"""Tests for the shared pagination dependency."""

import pytest
from pydantic import ValidationError

from app.routers.v1.common.pagination import (
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
    PaginationParams,
    get_pagination_params,
)


def test_get_pagination_params_returns_defaults():
    params = get_pagination_params()

    assert params == PaginationParams(skip=0, limit=DEFAULT_PAGE_LIMIT)


def test_get_pagination_params_accepts_custom_values():
    params = get_pagination_params(skip=10, limit=MAX_PAGE_LIMIT)

    assert params.skip == 10
    assert params.limit == MAX_PAGE_LIMIT


def test_pagination_params_requires_integer_values():
    with pytest.raises(ValidationError):
        PaginationParams(skip="oops", limit=10)
