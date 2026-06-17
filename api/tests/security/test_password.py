"""Tests for the password hashing utility."""

from app.security.password import hash_password


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
