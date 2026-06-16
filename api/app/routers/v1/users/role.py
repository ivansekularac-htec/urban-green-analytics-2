from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role
from app.schemas import RoleCreate, RoleResponse, RoleUpdate

role_router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@role_router.get("/", response_model=list[RoleResponse])
def get_roles(db: Session = Depends(get_db)):
    return db.query(Role).all()


@role_router.post(
    "/",
    response_model=RoleResponse,
    status_code=201,
)
def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
):
    role = Role(**role_data.model_dump())

    db.add(role)
    db.commit()
    db.refresh(role)

    return role


@role_router.put(
    "/{role_id}",
    response_model=RoleResponse,
)
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
):
    role = db.query(Role).filter(Role.id == role_id).first()

    if role is None:
        raise HTTPException(
            status_code=404,
            detail="Role not found",
        )

    for field, value in role_data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)

    return role
