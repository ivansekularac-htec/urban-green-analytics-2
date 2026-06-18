"""
Authentication service.

Handles credential verification and token issuing. User creation is handled
separately by the user CRUD service; this app is closed-type and has no public
registration.
"""

import jwt
from fastapi import HTTPException, status

from app.config import get_settings
from app.models.users.user import User
from app.repositories.users.user import UserRepository
from app.schemas.auth import TokenResponse
from app.security.jwt import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.security.password import verify_password

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect email or password.",
    headers={"WWW-Authenticate": "Bearer"},
)

_INVALID_REFRESH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid refresh token.",
    headers={"WWW-Authenticate": "Bearer"},
)


class AuthService:
    """
    Service for authentication and token issuing.
    """

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def authenticate(self, email: str, password: str) -> User:
        """
        Verify credentials and return the matching active user.

        Raises:
            HTTPException: 401 if the email is unknown, the password is wrong,
                or the account is inactive.
        """
        user = self.repository.get_by_email(email)

        # Use the same error for unknown email and wrong password to avoid
        # leaking which emails exist.
        if user is None or not verify_password(password, user.password_hash):
            raise _INVALID_CREDENTIALS

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user account.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    def login(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate the user and return an access + refresh token pair.
        """
        user = self.authenticate(email, password)
        return self._issue_tokens(user)

    def refresh(self, refresh_token: str) -> TokenResponse:
        """
        Issue a new token pair from a valid refresh token (rotation).

        Raises:
            HTTPException: 401 if the token is invalid, expired, not a refresh
                token, or the user no longer exists / is inactive.
        """
        try:
            claims = decode_token(refresh_token)
        except jwt.PyJWTError as exc:
            raise _INVALID_REFRESH from exc

        if claims.get("type") != REFRESH_TOKEN_TYPE:
            raise _INVALID_REFRESH

        try:
            user_id = int(claims.get("sub"))
        except (TypeError, ValueError) as exc:
            raise _INVALID_REFRESH from exc

        user = self.repository.get(user_id)

        if user is None or not user.is_active:
            raise _INVALID_REFRESH

        return self._issue_tokens(user)

    def _issue_tokens(self, user: User) -> TokenResponse:
        """Build a fresh access + refresh token pair for the user."""
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            roles=self._role_names(user),
        )
        refresh_token = create_refresh_token(user_id=user.id)
        expires_in = get_settings().access_token_expire_minutes * 60

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    @staticmethod
    def _role_names(user: User) -> list[str]:
        """Return the sorted, de-duplicated role names assigned to the user."""
        return sorted({user_role.role.name for user_role in user.user_roles})
