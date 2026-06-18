"""
Password hashing utilities.

Passwords are hashed with PBKDF2-HMAC-SHA256 and stored in the format
``pbkdf2_sha256$<salt>$<hash>``. The same parameters are used for hashing
and verification.
"""

import hashlib
import secrets

_ALGORITHM = "sha256"
_ITERATIONS = 100_000
_PREFIX = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using PBKDF2.
    """
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        _ALGORITHM,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _ITERATIONS,
    ).hex()

    return f"{_PREFIX}${salt}${password_hash}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verify a plain-text password against a stored PBKDF2 hash.

    Returns False for any malformed or unrecognized hash instead of raising,
    so callers can treat verification failure uniformly.
    """
    try:
        prefix, salt, expected_hash = stored_hash.split("$")
    except (ValueError, AttributeError):
        return False

    if prefix != _PREFIX:
        return False

    computed_hash = hashlib.pbkdf2_hmac(
        _ALGORITHM,
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        _ITERATIONS,
    ).hex()

    return secrets.compare_digest(computed_hash, expected_hash)
