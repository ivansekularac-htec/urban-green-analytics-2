"""
role_service.py
Service functions for role CRUD operations.

This module contains database operations for creating, reading,
updating, and deleting Role records.
"""

from sqlalchemy.orm import Session

from app.models.users.role import Role
from app.schemas.users.role import RoleCreate, RoleUpdate


def create_role(db: Session, role_data: RoleCreate) -> Role:
    """Create a new role.

    Args:
        db: Active database session.
        role_data: Role data received from the API request.

    Returns:
        Role: Created role instance.
    """
    role = Role(**role_data.model_dump())

    db.add(role)
    db.commit()
    db.refresh(role)

    return role


def get_roles(db: Session) -> list[Role]:
    """Return all roles.

    Args:
        db: Active database session.

    Returns:
        list[Role]: List of role records.
    """
    return db.query(Role).all()


def get_role_by_id(db: Session, role_id: int) -> Role | None:
    """Return a role by ID.

    Args:
        db: Active database session.
        role_id: Role identifier.

    Returns:
        Role | None: Role record if found, otherwise None.
    """
    return db.get(Role, role_id)


def update_role(db: Session, role: Role, role_data: RoleUpdate) -> Role:
    """Update an existing role.

    Args:
        db: Active database session.
        role: Existing role instance.
        role_data: Updated role data.

    Returns:
        Role: Updated role instance.
    """
    update_data = role_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)

    return role


def delete_role(db: Session, role: Role) -> None:
    """Delete an existing role.

    Args:
        db: Active database session.
        role: Existing role instance.
    """
    db.delete(role)
    db.commit()
