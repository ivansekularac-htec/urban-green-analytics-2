"""Tests for the generic ``BaseRepository`` CRUD helpers."""

from unittest.mock import MagicMock

import pytest

from app.models.crops.crop_category import CropCategory
from app.repositories.base_repository import BaseRepository


@pytest.fixture
def session():
    return MagicMock()


@pytest.fixture
def repository(session):
    return BaseRepository(CropCategory, session)


def test_get_delegates_to_session_get(session, repository):
    session.get.return_value = "item"

    result = repository.get(7)

    session.get.assert_called_once_with(CropCategory, 7)
    assert result == "item"


def test_list_uses_pagination_and_returns_list(session, repository):
    session.scalars.return_value.all.return_value = ["a", "b"]

    result = repository.list(skip=5, limit=10)

    session.scalars.assert_called_once()
    assert result == ["a", "b"]


def test_list_default_pagination(session, repository):
    session.scalars.return_value.all.return_value = []

    assert repository.list() == []


def test_create_instantiates_model_and_persists(session, repository):
    item = repository.create({"id": 1, "name": "abc"})

    assert isinstance(item, CropCategory)
    assert item.id == 1
    assert item.name == "abc"
    session.add.assert_called_once_with(item)
    session.flush.assert_called_once()
    session.refresh.assert_called_once_with(item)


def test_update_assigns_fields_and_refreshes(session, repository):
    item = CropCategory(id=1, name="old")

    result = repository.update(item, {"name": "new"})

    assert result is item
    assert item.name == "new"
    session.flush.assert_called_once()
    session.refresh.assert_called_once_with(item)


def test_delete_removes_item_and_flushes(session, repository):
    item = CropCategory(id=1, name="x")

    repository.delete(item)

    session.delete.assert_called_once_with(item)
    session.flush.assert_called_once()


def test_commit_and_rollback_proxy_to_session(session, repository):
    repository.commit()
    repository.rollback()

    session.commit.assert_called_once()
    session.rollback.assert_called_once()
