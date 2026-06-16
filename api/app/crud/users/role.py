"""
CRUD operations for roles.

This module provides functions for creating, retrieving,
updating, and deleting role records in the database.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users.role import Role
from app.schemas.users.role import RoleCreate, RoleUpdate


def create(
    db: Session,
    payload: RoleCreate,
) -> Role:
    """
    Create a new role.

    Args:
        db: Active database session.
        payload: Role data used to create the record.

    Returns:
        The newly created role instance.
    """

    obj = Role(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    role_id: int,
) -> Role | None:
    """
    Retrieve a role by its ID.

    Args:
        db: Active database session.
        role_id: Unique identifier of the role.

    Returns:
        The role instance if found, otherwise None.
    """

    return db.get(Role, role_id)


def get_all(
    db: Session,
) -> list[Role]:
    """
    Retrieve all roles.

    Args:
        db: Active database session.

    Returns:
        A list of all role records.
    """

    return list(db.scalars(select(Role)).all())


def update(
    db: Session,
    role: Role,
    payload: RoleUpdate,
) -> Role:
    """
    Update an existing role.

    Args:
        db: Active database session.
        role: Existing role instance to update.
        payload: Data containing the fields to be updated.

    Returns:
        The updated role instance.
    """

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)

    return role


def delete(
    db: Session,
    role: Role,
) -> None:
    """
    Delete an existing role.

    Args:
        db: Active database session.
        role: Role instance to delete.

    Returns:
        None.
    """

    db.delete(role)
    db.commit()
