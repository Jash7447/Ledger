from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import get_dashboard

router = APIRouter()


@router.get("", response_model=DashboardResponse)
def dashboard(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    month: Annotated[str | None, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")] = None,
) -> DashboardResponse:
    if month is not None and month.startswith("0000"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Month year must be greater than zero",
        )
    return get_dashboard(db, current_user.id, month)
