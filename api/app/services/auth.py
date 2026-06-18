"""
Authentication service.
"""

from fastapi import HTTPException, status

from app.repositories.users.user import UserRepository
from app.security.jwt import create_access_token
from app.security.password import verify_password


class AuthService:
    """
    Service for authentication operations.
    """

    def __init__(
        self,
        user_repository: UserRepository,
    ):
        self.user_repository = user_repository

    def login(
        self,
        *,
        email: str,
        password: str,
    ) -> str:
        """
        Authenticate a user and return a JWT token.
        """
        user = self.user_repository.get_by_email(
            email,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive",
            )

        return create_access_token(
            user_id=user.id,
            email=user.email,
        )
