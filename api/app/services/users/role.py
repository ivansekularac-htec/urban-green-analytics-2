from sqlalchemy.orm import Session

from app.models.users.role import Role
from app.schemas.users.role import RoleCreate, RoleUpdate


def get_roles(db: Session) -> list[Role]:
    """Query and return all roles from the database."""
    return db.query(Role).all()


def get_role(db: Session, role_id: int) -> Role | None:
    """Return a single role by ID, or None if not found."""
    return db.query(Role).filter(Role.id == role_id).first()


def create_role(db: Session, payload: RoleCreate) -> Role:
    """Persist a new role to the database and return it."""
    role = Role(**payload.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_role(db: Session, role: Role, payload: RoleUpdate) -> Role:
    """Apply partial field updates to an existing role and return it."""
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role: Role) -> None:
    """Delete a role from the database."""
    db.delete(role)
    db.commit()
