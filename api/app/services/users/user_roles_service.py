"""
user_role_service.py
Service functions for user role CRUD operations.

This module contains database operations for creating, reading,
updating, and deleting UserRole records.
"""

from sqlalchemy.orm import Session

from app.models.users.user_roles import UserRole
from app.schemas.users.user_roles import UserRoleCreate, UserRoleUpdate


def create_user_role(db: Session, user_role_data: UserRoleCreate) -> UserRole:
    """Create a new user role assignment."""
    user_role = UserRole(**user_role_data.model_dump())

    db.add(user_role)
    db.commit()
    db.refresh(user_role)

    return user_role


def get_user_roles(db: Session) -> list[UserRole]:
    """Return all user role assignments."""
    return db.query(UserRole).all()


def update_user_role(
    db: Session,
    user_role: UserRole,
    user_role_data: UserRoleUpdate,
) -> UserRole:
    """Update an existing user role assignment."""
    update_data = user_role_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user_role, field, value)

    db.commit()
    db.refresh(user_role)

    return user_role


def delete_user_role(db: Session, user_role: UserRole) -> None:
    """Delete an existing user role assignment."""
    db.delete(user_role)
    db.commit()
