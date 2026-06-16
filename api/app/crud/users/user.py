"""
CRUD operations for users.

This module provides functions for creating, retrieving,
updating, and deleting user records in the database.
"""

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users.user import User
from app.schemas.users.user import UserCreate, UserUpdate

password_hash = PasswordHash.recommended()


def create(
    db: Session,
    payload: UserCreate,
) -> User:
    """
    Create a new user.

    The user's password is securely hashed before being stored
    in the database.

    Args:
        db: Active database session.
        payload: User data used to create the record.

    Returns:
        The newly created user instance.
    """

    obj = User(
        **payload.model_dump(exclude={"password"}),
        password_hash=password_hash.hash(payload.password),
    )

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    user_id: int,
) -> User | None:
    """
    Retrieve a user by its ID.

    Args:
        db: Active database session.
        user_id: Unique identifier of the user.

    Returns:
        The user instance if found, otherwise None.
    """

    return db.get(User, user_id)


def get_all(
    db: Session,
) -> list[User]:
    """
    Retrieve all users.

    Args:
        db: Active database session.

    Returns:
        A list of all user records.
    """

    return list(db.scalars(select(User)).all())


def update(
    db: Session,
    user: User,
    payload: UserUpdate,
) -> User:
    """
    Update an existing user.

    Args:
        db: Active database session.
        user: Existing user instance to update.
        payload: Data containing the fields to be updated.

    Returns:
        The updated user instance.
    """

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


def delete(
    db: Session,
    user: User,
) -> None:
    """
    Delete an existing user.

    Args:
        db: Active database session.
        user: User instance to delete.

    Returns:
        None.
    """

    db.delete(user)
    db.commit()
