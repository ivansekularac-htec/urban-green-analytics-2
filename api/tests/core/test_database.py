"""Tests for the database session and connection helpers."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app import database


def test_get_db_yields_session_and_closes_it():
    fake_session = MagicMock()

    with patch.object(database, "SessionLocal", return_value=fake_session):
        generator = database.get_db()
        session = next(generator)

        assert session is fake_session

        with pytest.raises(StopIteration):
            next(generator)

    fake_session.close.assert_called_once()


def test_get_db_closes_session_when_consumer_raises():
    fake_session = MagicMock()

    with patch.object(database, "SessionLocal", return_value=fake_session):
        generator = database.get_db()
        next(generator)
        generator.close()

    fake_session.close.assert_called_once()


def test_verify_database_connection_succeeds():
    connection = MagicMock()
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection

    with patch.object(database, "engine", engine):
        database.verify_database_connection()

    connection.execute.assert_called_once()


def test_verify_database_connection_logs_and_reraises_on_failure():
    engine = MagicMock()
    engine.connect.side_effect = SQLAlchemyError("connection refused")

    with patch.object(database, "engine", engine), pytest.raises(SQLAlchemyError):
        database.verify_database_connection()
