"""
user_service.py
Service functions for user CRUD operations.

This module contains database operations for creating, reading,
updating, and deleting User records.
"""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.users.user import User
from app.schemas.users.user import UserCreate, UserPasswordUpdate, UserUpdate


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user."""
    user_dict = user_data.model_dump()

    password = user_dict.pop("password")

    user = User(
        **user_dict,
        password_hash=hash_password(password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_users(db: Session) -> list[User]:
    """Return all users."""
    return db.query(User).all()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Return a user by ID."""
    return db.get(User, user_id)


def update_user(
    db: Session,
    user: User,
    user_data: UserUpdate,
) -> User:
    """Update an existing user."""
    update_data = user_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


def update_user_password(
    db: Session,
    user: User,
    password_data: UserPasswordUpdate,
) -> User:
    """Update an existing user's password."""
    user.password_hash = hash_password(password_data.password)

    db.commit()
    db.refresh(user)

    return user


def delete_user(db: Session, user: User) -> None:
    """Delete an existing user."""
    db.delete(user)
    db.commit()
