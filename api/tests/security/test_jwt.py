"""Tests for the JWT encode/decode helpers."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException

from app.config import get_settings
from app.security.jwt import create_access_token, decode_access_token


def test_create_and_decode_access_token_round_trip():
    token = create_access_token(user_id=42)

    assert decode_access_token(token) == 42


def test_decode_access_token_rejects_tampered_token():
    token = create_access_token(user_id=42)
    # Flip a character in the signature segment.
    header, payload, signature = token.split(".")
    tampered = ".".join(
        [header, payload, signature[:-2] + ("aa" if signature[-2:] != "aa" else "bb")]
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(tampered)

    assert exc_info.value.status_code == 401


def test_decode_access_token_rejects_expired_token():
    settings = get_settings()
    expired_at = datetime.now(UTC) - timedelta(minutes=1)
    expired_token = jwt.encode(
        {"sub": "1", "exp": expired_at},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(expired_token)

    assert exc_info.value.status_code == 401


def test_decode_access_token_rejects_malformed_token():
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("not-a-jwt-at-all")

    assert exc_info.value.status_code == 401


def test_decode_access_token_rejects_missing_sub_claim():
    settings = get_settings()
    token = jwt.encode(
        {"exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(token)

    assert exc_info.value.status_code == 401
