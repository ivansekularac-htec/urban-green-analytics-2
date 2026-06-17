from sqlalchemy.orm import Session

from app.models.users.user_roles import UserRole
from app.schemas.users.user_roles import UserRoleCreate, UserRoleUpdate


def get_user_roles(db: Session) -> list[UserRole]:
    """Query and return all user roles from the database."""
    return db.query(UserRole).all()


def get_user_role(db: Session, user_role_id: int) -> UserRole | None:
    """Return a single user role by ID, or None if not found."""
    return db.query(UserRole).filter(UserRole.id == user_role_id).first()


def create_user_role(db: Session, payload: UserRoleCreate) -> UserRole:
    """Persist a new user role to the database and return it."""
    user_role = UserRole(**payload.model_dump())
    db.add(user_role)
    db.commit()
    db.refresh(user_role)
    return user_role


def update_user_role(db: Session, user_role: UserRole, payload: UserRoleUpdate) -> UserRole:
    """Apply partial field updates to an existing user role and return it."""
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user_role, field, value)
    db.commit()
    db.refresh(user_role)
    return user_role


def delete_user_role(db: Session, user_role: UserRole) -> None:
    """Delete a user role from the database."""
    db.delete(user_role)
    db.commit()
