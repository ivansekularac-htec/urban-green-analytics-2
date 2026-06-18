"""Tests for the password hashing utility."""

from app.security.password import hash_password, verify_password


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


def test_verify_password_accepts_correct_password():
    encoded = hash_password("hunter2")

    assert verify_password("hunter2", encoded) is True


def test_verify_password_rejects_wrong_password():
    encoded = hash_password("hunter2")

    assert verify_password("wrong", encoded) is False


def test_verify_password_rejects_malformed_hash():
    assert verify_password("hunter2", "not-a-valid-hash") is False


def test_verify_password_rejects_unknown_prefix():
    encoded = hash_password("hunter2")
    _, salt, digest = encoded.split("$")

    assert verify_password("hunter2", f"bcrypt${salt}${digest}") is False
