"""
auth_service.py
Service functions for authentication.

This module contains business logic for user registration,
login, password verification, and JWT token creation.
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.users.user import UserRepository
from app.schemas.auth import RegisterRequest, Token
from app.security.password import create_access_token, hash_password, verify_password


class AuthService:
    """
    Service for authentication operations.

    This service handles user registration, user login,
    password verification, and JWT token generation.
    """

    def __init__(self, db: Session):
        """
        Initialize authentication service.

        Args:
            db: Active database session.
        """
        self.user_repository = UserRepository(db)

    def register_user(
        self,
        register_data: RegisterRequest,
    ) -> Token:
        """
        Register a new user and return a JWT access token.

        Args:
            register_data: Registration request data.

        Returns:
            Token: JWT access token response.

        Raises:
            HTTPException: If a user with the same email already exists.
        """
        existing_user = self.user_repository.get_by_email(register_data.email)

        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists.",
            )

        try:
            user = self.user_repository.create(
                {
                    "email": register_data.email,
                    "full_name": register_data.full_name,
                    "password_hash": hash_password(register_data.password),
                    "is_active": True,
                },
            )
            self.user_repository.commit()

        except IntegrityError as exc:
            self.user_repository.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists.",
            ) from exc

        access_token = create_access_token(
            subject=str(user.id),
            roles=[],
        )

        return Token(access_token=access_token)

    def login_user(
        self,
        email: str,
        password: str,
    ) -> Token:
        """
        Authenticate a user and return a JWT access token.

        Args:
            login_data: Login request data.

        Returns:
            Token: JWT access token response.

        Raises:
            HTTPException: If credentials are invalid or user is inactive.
        """
        user = self.user_repository.get_by_email(email)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user account.",
            )

        roles = self.user_repository.get_role_names(user.id)

        access_token = create_access_token(
            subject=str(user.id),
            roles=roles,
        )

        return Token(access_token=access_token)
