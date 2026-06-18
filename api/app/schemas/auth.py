"""
auth.py
Pydantic schemas for authentication requests and responses.

This module defines schemas used for user registration, login,
and JWT token responses.
"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request schema used for user registration."""

    email: EmailStr
    full_name: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=255)


class LoginRequest(BaseModel):
    """Request schema used for user login."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=255)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    roles: list[str] = []
