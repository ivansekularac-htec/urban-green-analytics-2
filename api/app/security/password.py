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


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a plain-text password against a stored PBKDF2 hash.
    """
    try:
        algorithm, salt, password_hash = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        ).hex()

        return secrets.compare_digest(
            calculated_hash,
            password_hash,
        )

    except ValueError:
        return False
