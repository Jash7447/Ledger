from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.education import EducationReport
from app.services.education import get_education_report

router = APIRouter()


@router.get("", response_model=EducationReport)
def report(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> EducationReport:
    today = date.today()
    start = date_from or date(today.year, 1, 1)
    end = date_to or today
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from must be on or before date_to",
        )
    return get_education_report(db, current_user.id, start, end)
