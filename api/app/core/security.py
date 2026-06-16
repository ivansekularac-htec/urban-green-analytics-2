# app/core/security.py

"""
Security utilities.

Provides password hashing and verification helpers.
"""

import hashlib


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256.

    Args:
        password (str): Plain text password.

    Returns:
        str: Hashed password.
    """

    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password (str): Plain text password.
        hashed_password (str): Stored password hash.

    Returns:
        bool: True if passwords match.
    """

    return hash_password(plain_password) == hashed_password
