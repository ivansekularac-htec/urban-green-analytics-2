"""
roles.py
CRUD operations for Role entities.

This module provides database access functions for creating and retrieving
role records. It encapsulates SQLAlchemy queries and session interactions,
allowing API routes and services to work with Role objects without directly
managing database operations.

Functions:
    create: Create and persist a new role in the database.
    get: Retrieve a role by its primary key.
    get_all: Retrieve all roles from the database.
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
    Create and persist a new role.

    Args:
        db: Active database session.
        payload: Data used to create the role.

    Returns:
        The newly created Role instance.
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
        role_id: Primary key of the role.

    Returns:
        The matching Role instance if found, otherwise None.
    """
    return db.get(Role, role_id)


def get_all(
    db: Session,
) -> list[Role]:
    """
    Retrieve all roles from the database.

    Args:
        db: Active database session.

    Returns:
        A list containing all Role records.
    """
    return list(db.scalars(select(Role)).all())


def update(
    db: Session,
    role: Role,
    payload: RoleUpdate,
) -> Role:

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)

    return role


def delete(
    db: Session,
    role: Role,
) -> None:

    db.delete(role)
    db.commit()
