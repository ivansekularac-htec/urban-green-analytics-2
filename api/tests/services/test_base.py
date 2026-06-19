"""Tests for the generic ``BaseService`` business-logic layer."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.repositories.base_repository import BaseRepository
from app.services.base_service import BaseService


class _Create(BaseModel):
    name: str


class _Update(BaseModel):
    name: str | None = None


@pytest.fixture
def repository():
    return MagicMock(spec=BaseRepository)


@pytest.fixture
def service(repository):
    return BaseService(repository, "Widget")


def _integrity_error() -> IntegrityError:
    return IntegrityError("insert", params=None, orig=Exception("conflict"))


def test_get_returns_repository_result(repository, service):
    repository.get.return_value = "item"

    assert service.get(1) == "item"
    repository.get.assert_called_once_with(1)


def test_get_raises_404_when_missing(repository, service):
    repository.get.return_value = None

    with pytest.raises(HTTPException) as exc:
        service.get(1)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Widget" in exc.value.detail


def test_list_passes_pagination(repository, service):
    repository.list.return_value = ["a"]

    assert service.list(skip=2, limit=5) == ["a"]
    repository.list.assert_called_once_with(skip=2, limit=5, farm_ids=None)


def test_list_forwards_farm_ids(repository, service):
    repository.list.return_value = ["a"]

    assert service.list(skip=0, limit=10, farm_ids={1, 2}) == ["a"]
    repository.list.assert_called_once_with(skip=0, limit=10, farm_ids={1, 2})


def test_create_persists_payload_and_commits(repository, service):
    repository.create.return_value = "created"

    result = service.create(_Create(name="foo"))

    assert result == "created"
    repository.create.assert_called_once_with({"name": "foo"})
    repository.commit.assert_called_once()


def test_create_translates_integrity_error_to_409(repository, service):
    repository.create.side_effect = _integrity_error()

    with pytest.raises(HTTPException) as exc:
        service.create(_Create(name="foo"))

    assert exc.value.status_code == status.HTTP_409_CONFLICT
    repository.rollback.assert_called_once()


def test_update_applies_only_provided_fields(repository, service):
    repository.get.return_value = "item"
    repository.update.return_value = "updated"

    result = service.update(1, _Update(name="bar"))

    assert result == "updated"
    repository.update.assert_called_once_with("item", {"name": "bar"})
    repository.commit.assert_called_once()


def test_update_returns_existing_item_when_payload_is_empty(repository, service):
    repository.get.return_value = "item"

    result = service.update(1, _Update())

    assert result == "item"
    repository.update.assert_not_called()
    repository.commit.assert_not_called()


def test_update_translates_integrity_error_to_409(repository, service):
    repository.get.return_value = "item"
    repository.update.side_effect = _integrity_error()

    with pytest.raises(HTTPException) as exc:
        service.update(1, _Update(name="bar"))

    assert exc.value.status_code == status.HTTP_409_CONFLICT
    repository.rollback.assert_called_once()


def test_delete_removes_item_and_commits(repository, service):
    repository.get.return_value = "item"

    service.delete(1)

    repository.delete.assert_called_once_with("item")
    repository.commit.assert_called_once()


def test_delete_translates_integrity_error_to_409(repository, service):
    repository.get.return_value = "item"
    repository.delete.side_effect = _integrity_error()

    with pytest.raises(HTTPException) as exc:
        service.delete(1)

    assert exc.value.status_code == status.HTTP_409_CONFLICT
    repository.rollback.assert_called_once()
