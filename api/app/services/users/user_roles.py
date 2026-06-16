"""
Service layer for UserRole.

Handles role assignments for users, optionally scoped to a farm.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.farms.farm import Farm
from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.schemas.users.user_roles import (
    UserRoleCreate,
    UserRoleUpdate,
)


class UserRoleService:
    # -------------------------------------------------
    # READ
    # -------------------------------------------------

    def get(self, db: Session, user_role_id: int):
        """
        Retrieve a UserRole by ID.
        """

        obj = db.query(UserRole).filter(UserRole.id == user_role_id).first()

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User role not found",
            )

        return obj

    def get_all(self, db: Session):
        """
        Retrieve all UserRole records.
        """

        return db.query(UserRole).all()

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    def create(self, db: Session, data: UserRoleCreate):
        """
        Create a UserRole assignment.
        """

        user = db.query(User).filter(User.id == data.user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        role = db.query(Role).filter(Role.id == data.role_id).first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

        if data.farm_id is not None:
            farm = db.query(Farm).filter(Farm.id == data.farm_id).first()

            if not farm:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Farm not found",
                )

        existing = (
            db.query(UserRole)
            .filter(UserRole.user_id == data.user_id)
            .filter(UserRole.role_id == data.role_id)
            .filter(UserRole.farm_id == data.farm_id)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has this role assignment",
            )

        obj = UserRole(**data.model_dump())

        db.add(obj)
        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------

    def update(self, db: Session, user_role_id: int, data: UserRoleUpdate):
        """
        Update a UserRole assignment.
        """

        obj = self.get(db, user_role_id)

        update_data = data.model_dump(exclude_unset=True)

        user_id = update_data.get(
            "user_id",
            obj.user_id,
        )

        role_id = update_data.get(
            "role_id",
            obj.role_id,
        )

        farm_id = update_data.get(
            "farm_id",
            obj.farm_id,
        )

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        role = db.query(Role).filter(Role.id == role_id).first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

        if farm_id is not None:
            farm = db.query(Farm).filter(Farm.id == farm_id).first()

            if not farm:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Farm not found",
                )

        duplicate = (
            db.query(UserRole)
            .filter(UserRole.user_id == user_id)
            .filter(UserRole.role_id == role_id)
            .filter(UserRole.farm_id == farm_id)
            .filter(UserRole.id != user_role_id)
            .first()
        )

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has this role assignment",
            )

        for key, value in update_data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # DELETE
    # -------------------------------------------------

    def delete(self, db: Session, user_role_id: int):
        """
        Delete a UserRole assignment.
        """

        obj = self.get(db, user_role_id)

        db.delete(obj)
        db.commit()
