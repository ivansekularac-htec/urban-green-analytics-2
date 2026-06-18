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


def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, digest = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()
    return secrets.compare_digest(candidate, digest)
