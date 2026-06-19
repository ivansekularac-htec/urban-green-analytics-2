"""
Password hashing utilities.
"""

import hashlib
import hmac
import secrets

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using PBKDF2.
    """
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _ITERATIONS,
    ).hex()

    return f"{_ALGORITHM}${salt}${password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a plain-text password against a previously hashed value.

    Returns False on any malformed input rather than raising, so callers
    can treat auth failures uniformly without try/except.
    """
    parts = stored_hash.split("$")
    if len(parts) != 3 or parts[0] != _ALGORITHM:
        return False

    _, salt, expected = parts
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _ITERATIONS,
    ).hex()

    return hmac.compare_digest(candidate, expected)
