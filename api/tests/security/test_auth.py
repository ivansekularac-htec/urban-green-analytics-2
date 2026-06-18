"""Tests for authentication security helpers."""

import pytest
from fastapi import HTTPException

from app.security.dependencies import require_roles
from app.security.jwt import create_access_token, decode_access_token
from app.security.password import hash_password, verify_password


def test_create_and_decode_access_token():
    token = create_access_token(
        {
            "sub": "1",
            "email": "admin@example.com",
            "roles": ["Admin"],
            "farm_ids": [],
        }
    )

    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["email"] == "admin@example.com"
    assert payload["roles"] == ["Admin"]
    assert payload["farm_ids"] == []


def test_decode_invalid_token_returns_none():
    payload = decode_access_token("invalid-token")

    assert payload is None


def test_verify_password_returns_true_for_valid_password():
    password_hash = hash_password("admin12345")

    assert verify_password("admin12345", password_hash) is True


def test_verify_password_returns_false_for_invalid_password():
    password_hash = hash_password("admin12345")

    assert verify_password("wrong-password", password_hash) is False


def test_require_roles_allows_admin():
    dependency = require_roles("operations")

    payload = {"roles": ["Admin"]}

    result = dependency(payload)

    assert result == payload


def test_require_roles_allows_matching_role_case_insensitive():
    dependency = require_roles("farm manager")

    payload = {"roles": ["Farm Manager"]}

    result = dependency(payload)

    assert result == payload


def test_require_roles_blocks_missing_role():
    dependency = require_roles("admin")

    payload = {"roles": ["Operations"]}

    with pytest.raises(HTTPException) as exc:
        dependency(payload)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Insufficient permissions"
