"""
Service layer for User.

Handles business logic and database operations for users.

Ensures email uniqueness and password hashing.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.users.user import User
from app.schemas.users.user import UserCreate, UserPasswordUpdate, UserUpdate


class UserService:
    # -------------------------------------------------
    # READ
    # -------------------------------------------------

    def get(self, db: Session, user_id: int):
        """
        Retrieve a single User by ID.

        Args:
            db (Session): Active DB session.
            user_id (int): User ID.

        Returns:
            User: Requested entity.

        Raises:
            HTTPException: 404 if user does not exist.
        """

        obj = db.query(User).filter(User.id == user_id).first()

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return obj

    def get_all(self, db: Session):
        """
        Retrieve all users.

        Args:
            db (Session): Active DB session.

        Returns:
            list[User]: All users.
        """

        return db.query(User).all()

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    def create(self, db: Session, data: UserCreate):
        """
        Create a new user.

        Ensures email uniqueness and hashes password.

        Args:
            db (Session): Active DB session.
            data (UserCreate): Input payload.

        Returns:
            User: Created entity.

        Raises:
            HTTPException: 400 if email already exists.
        """

        existing = db.query(User).filter(User.email == data.email).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        payload = data.model_dump(exclude={"password"})

        obj = User(
            **payload,
            password_hash=hash_password(data.password),
        )

        db.add(obj)
        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------

    def update(
        self,
        db: Session,
        user_id: int,
        data: UserUpdate,
    ):
        """
        Update User.

        Args:
            db (Session): Active DB session.
            user_id (int): User ID.
            data (UserUpdate): Update payload.

        Returns:
            User: Updated entity.

        Raises:
            HTTPException: 404 if user does not exist.
            HTTPException: 400 if email already exists.
        """

        obj = self.get(db, user_id)

        update_data = data.model_dump(exclude_unset=True)

        if "email" in update_data:
            existing = (
                db.query(User)
                .filter(User.email == update_data["email"])
                .filter(User.id != user_id)
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists",
                )

        for key, value in update_data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)

        return obj

    def update_password(
        self,
        db: Session,
        user_id: int,
        data: UserPasswordUpdate,
    ):
        """
        Update user password.

        Args:
            db (Session): Active DB session.
            user_id (int): User ID.
            data (UserPasswordUpdate): New password payload.

        Returns:
            User: Updated user.

        Raises:
            HTTPException: 404 if user not found.
        """

        user = self.get(db, user_id)

        user.password_hash = hash_password(data.password)

        db.commit()
        db.refresh(user)

        return user

    # -------------------------------------------------
    # DELETE
    # -------------------------------------------------

    def delete(self, db: Session, user_id: int):
        """
        Delete User.

        Args:
            db (Session): Active DB session.
            user_id (int): User ID.

        Raises:
            HTTPException: 404 if user does not exist.
        """

        obj = self.get(db, user_id)

        db.delete(obj)
        db.commit()

        return None
