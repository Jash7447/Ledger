from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.budget import BudgetCreate, BudgetProgress, BudgetUpdate
from app.services.budgets import (
    create_budget,
    delete_budget,
    get_budget_with_progress,
    list_budgets_with_progress,
    update_budget,
)

router = APIRouter()


@router.get("", response_model=list[BudgetProgress])
def list_all(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    month: Annotated[str, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")],
) -> list[BudgetProgress]:
    _validate_year(month)
    return list_budgets_with_progress(db, current_user.id, month)


@router.post("", response_model=BudgetProgress, status_code=status.HTTP_201_CREATED)
def create(
    data: BudgetCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BudgetProgress:
    return create_budget(db, current_user.id, data)


@router.get("/{budget_id}", response_model=BudgetProgress)
def get(
    budget_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BudgetProgress:
    return get_budget_with_progress(db, current_user.id, budget_id)


@router.patch("/{budget_id}", response_model=BudgetProgress)
def update(
    budget_id: UUID,
    data: BudgetUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BudgetProgress:
    return update_budget(db, current_user.id, budget_id, data)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    budget_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    delete_budget(db, current_user.id, budget_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _validate_year(month: str) -> None:
    if month.startswith("0000"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Month year must be greater than zero",
        )
