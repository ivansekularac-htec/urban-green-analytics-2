"""
CRUD operations for user role assignments.

This module provides functions for creating, retrieving,
updating, and deleting user role assignment records in the database.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.helpers import commit_or_409
from app.models.users.user_roles import UserRole
from app.schemas.users.user_roles import UserRoleCreate, UserRoleUpdate


def create(
    db: Session,
    payload: UserRoleCreate,
) -> UserRole:
    """
    Create a new user role assignment.

    Args:
        db: Active database session.
        payload: User role assignment data used to create the record.

    Returns:
        The newly created user role assignment instance.
    """

    obj = UserRole(**payload.model_dump())

    db.add(obj)
    commit_or_409(db)
    db.refresh(obj)

    return obj


def get(
    db: Session,
    user_role_id: int,
) -> UserRole | None:
    """
    Retrieve a user role assignment by its ID.

    Args:
        db: Active database session.
        user_role_id: Unique identifier of the user role assignment.

    Returns:
        The user role assignment instance if found, otherwise None.
    """

    return db.get(UserRole, user_role_id)


def get_all(
    db: Session,
    skip: int,
    limit: int,
) -> list[UserRole]:
    """
    Retrieve all user role assignments.

    Args:
        db: Active database session.

    Returns:
        A list of all user role assignment records.
    """

    stmt = select(UserRole).offset(skip).limit(limit)

    return db.scalars(stmt).all()


def update(
    db: Session,
    user_role: UserRole,
    payload: UserRoleUpdate,
) -> UserRole:
    """
    Update an existing user role assignment.

    Args:
        db: Active database session.
        user_role: Existing user role assignment instance to update.
        payload: Data containing the fields to be updated.

    Returns:
        The updated user role assignment instance.
    """

    for field, value in payload.model_dump(
        exclude_unset=True,
    ).items():
        setattr(user_role, field, value)

    commit_or_409(db)
    db.refresh(user_role)

    return user_role


def delete(
    db: Session,
    user_role: UserRole,
) -> None:
    """
    Delete an existing user role assignment.

    Args:
        db: Active database session.
        user_role: User role assignment instance to delete.

    Returns:
        None.
    """

    db.delete(user_role)
    commit_or_409(db)
