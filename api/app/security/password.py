"""
Password hashing utilities.
"""

import hashlib
import secrets


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using PBKDF2.
    """
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()

    return f"pbkdf2_sha256${salt}${password_hash}"


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored PBKDF2 hash.
    """
    try:
        algorithm, salt, stored_hash = hashed_password.split("$")
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()

    return secrets.compare_digest(password_hash, stored_hash)
