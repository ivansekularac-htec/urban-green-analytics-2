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
    stored = hash_password("hunter2hunter2")
    assert verify_password("hunter2hunter2", stored) is True


def test_verify_password_rejects_wrong_password():
    stored = hash_password("hunter2hunter2")
    assert verify_password("wrong-password", stored) is False


def test_verify_password_rejects_invalid_hash_format():
    assert verify_password("hunter2hunter2", "not-a-valid-hash") is False


def test_verify_password_rejects_unsupported_algorithm():
    assert verify_password("hunter2hunter2", "bcrypt$salt$digest") is False
