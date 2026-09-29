from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.analytics import AnalyticsResponse
from app.services.analytics import get_analytics

router = APIRouter()


@router.get("", response_model=AnalyticsResponse)
def analytics(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    date_from: Annotated[date, Query()],
    date_to: Annotated[date, Query()],
) -> AnalyticsResponse:
    if date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_to must be on or after date_from",
        )
    return get_analytics(db, current_user.id, date_from, date_to)
