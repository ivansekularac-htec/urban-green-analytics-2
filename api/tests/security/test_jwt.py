"""Tests for the JWT token utilities."""

import time

import jwt
import pytest

from app.config import get_settings
from app.security.jwt import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_create_and_decode_access_token_roundtrip():
    token = create_access_token(user_id=7, email="admin@uga.com", roles=["Admin"])

    claims = decode_token(token)

    assert claims["sub"] == "7"
    assert claims["email"] == "admin@uga.com"
    assert claims["roles"] == ["Admin"]
    assert claims["type"] == ACCESS_TOKEN_TYPE
    assert "exp" in claims
    assert "iat" in claims


def test_create_refresh_token_has_refresh_type_and_no_roles():
    token = create_refresh_token(user_id=7)

    claims = decode_token(token)

    assert claims["sub"] == "7"
    assert claims["type"] == REFRESH_TOKEN_TYPE
    assert "roles" not in claims


def test_decode_rejects_bad_signature():
    settings = get_settings()
    forged = jwt.encode(
        {"sub": "1"},
        "another-secret-key-that-is-at-least-32-bytes-long",
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.PyJWTError):
        decode_token(forged)


def test_decode_rejects_expired_token():
    settings = get_settings()
    payload = {"sub": "1", "exp": int(time.time()) - 60}
    expired = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired)
