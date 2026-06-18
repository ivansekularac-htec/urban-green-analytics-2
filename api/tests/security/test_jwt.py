"""Tests for JWT creation and decoding."""

from datetime import UTC, datetime, timedelta

import pytest
from jose import JWTError, jwt

from app.config import get_settings
from app.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_create_access_token_contains_expected_claims():
    token = create_access_token(
        user_id=1,
        email="alice@example.com",
        roles=["admin", "viewer"],
    )
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["email"] == "alice@example.com"
    assert payload["roles"] == ["admin", "viewer"]
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_refresh_token_contains_expected_claims():
    token = create_refresh_token(user_id=42)
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_decode_token_rejects_tampered_token():
    token = create_access_token(
        user_id=1,
        email="alice@example.com",
        roles=["admin"],
    )
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises(JWTError):
        decode_token(tampered)


def test_decode_token_rejects_expired_token():
    settings = get_settings()
    expired = jwt.encode(
        {
            "sub": "1",
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(JWTError):
        decode_token(expired)
