from fastapi import APIRouter, HTTPException, status

from app.crud.harvests import quality_grade as quality_grade_crud
from app.routers.helpers import DBSession, PaginationDep
from app.schemas.harvests.quality_grade import QualityGradeCreate, QualityGradeResponse

router = APIRouter(prefix="/quality_grade", tags=["Quality Grade"])


@router.post(
    "/",
    response_model=QualityGradeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_grade(
    payload: QualityGradeCreate,
    db: DBSession,
) -> QualityGradeResponse:
    """
    Create a new quality grade.

    Args:
        payload: Quality grade data to create.
        db: Active database session.

    Returns:
        The newly created quality grade.
    """
    return quality_grade_crud.create(db, payload)


@router.get(
    "/{quality_grade_id}",
    response_model=QualityGradeResponse,
)
def get_quality_grade(
    quality_grade_id: int,
    db: DBSession,
) -> QualityGradeResponse:
    """
    Retrieve a quality grade by its ID.

    Args:
        quality_grade_id: Unique identifier of the quality grade.
        db: Active database session.

    Returns:
        The requested quality grade.

    Raises:
        HTTPException: If the quality grade does not exist.
    """
    quality_grade = quality_grade_crud.get(db, quality_grade_id)

    if quality_grade is None:
        raise HTTPException(
            status_code=404,
            detail="Quality Grade not found",
        )

    return quality_grade


@router.get(
    "/",
    response_model=list[QualityGradeResponse],
)
def get_quality_grades(
    db: DBSession,
    pagination: PaginationDep,
) -> list[QualityGradeResponse]:
    """
    Retrieve all quality grades.

    Args:
        db: Active database session.

    Returns:
        A list of all quality grades.
    """
    return quality_grade_crud.get_all(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
    )
