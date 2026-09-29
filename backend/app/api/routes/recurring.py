from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.recurring import RecurringCreate, RecurringResponse, RecurringUpdate
from app.services.recurring import (
    create_recurring,
    delete_recurring,
    get_recurring,
    list_recurring,
    update_recurring,
)

router = APIRouter()


@router.get("", response_model=list[RecurringResponse])
def list_all(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    is_active: Annotated[bool | None, Query()] = None,
) -> list[RecurringResponse]:
    return list_recurring(db, current_user.id, is_active)


@router.post("", response_model=RecurringResponse, status_code=status.HTTP_201_CREATED)
def create(
    data: RecurringCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> RecurringResponse:
    return create_recurring(db, current_user.id, data)


@router.get("/{recurring_id}", response_model=RecurringResponse)
def get(
    recurring_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> RecurringResponse:
    return get_recurring(db, current_user.id, recurring_id)


@router.patch("/{recurring_id}", response_model=RecurringResponse)
def update(
    recurring_id: UUID,
    data: RecurringUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> RecurringResponse:
    return update_recurring(db, current_user.id, recurring_id, data)


@router.delete("/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    recurring_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    delete_recurring(db, current_user.id, recurring_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
