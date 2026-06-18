from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app


def test_lifespan_verifies_database_connection_on_startup():
    session_mock = MagicMock()

    with (
        patch("app.main.verify_database_connection") as verify,
        patch("app.main.ensure_superuser") as ensure_superuser,
        patch("app.main.SessionLocal", return_value=session_mock),
        TestClient(app),
    ):
        verify.assert_called_once()
        ensure_superuser.assert_called_once()
        session_mock.close.assert_called_once()
