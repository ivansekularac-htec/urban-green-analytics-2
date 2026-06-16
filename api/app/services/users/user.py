import bcrypt
from sqlalchemy.orm import Session

from app.models.users.user import User
from app.schemas.users.user import UserCreate, UserUpdate


def _hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt (salted, work-factor hardened)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def get_users(db: Session) -> list[User]:
    """Query and return all users from the database."""
    return db.query(User).all()


def get_user(db: Session, user_id: int) -> User | None:
    """Return a single user by ID, or None if not found."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, payload: UserCreate) -> User:
    """Persist a new user to the database and return it."""
    data = payload.model_dump(exclude={"password"})
    data["password_hash"] = _hash_password(payload.password)
    user = User(**data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    """Apply partial field updates to an existing user and return it."""
    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        user.password_hash = _hash_password(data.pop("password"))
    for field, value in data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    """Delete a user from the database."""
    db.delete(user)
    db.commit()
