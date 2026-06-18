"""Tests for the password hashing utility."""

from datetime import timedelta

import pytest
from jose import JWTError

from app.security.password import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_uses_pbkdf2_format():
    encoded = hash_password("correct horse battery staple")

    algorithm, salt, digest = encoded.split("$")

    assert algorithm == "pbkdf2_sha256"
    assert len(salt) == 32
    assert len(digest) == 64


def test_hash_password_uses_unique_salt_per_call():
    first = hash_password("hunter2")
    second = hash_password("hunter2")

    assert first != second


def test_verify_password_returns_true_for_valid_password():
    hashed_password = hash_password("password123")

    assert verify_password("password123", hashed_password) is True


def test_verify_password_returns_false_for_wrong_password():
    hashed_password = hash_password("password123")

    assert verify_password("wrongpassword", hashed_password) is False


def test_verify_password_returns_false_for_invalid_hash_format():
    assert verify_password("password123", "invalid-hash") is False


def test_create_and_decode_access_token():
    token = create_access_token(
        subject="1",
        roles=["Admin"],
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "1"
    assert payload["roles"] == ["Admin"]


def test_decode_expired_access_token_raises_jwt_error():
    token = create_access_token(
        subject="1",
        roles=["Admin"],
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(JWTError):
        decode_access_token(token)
