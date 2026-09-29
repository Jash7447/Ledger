from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.goal import GoalCreate, GoalResponse, GoalUpdate
from app.services.goals import create_goal, delete_goal, get_goal, list_goals, update_goal

router = APIRouter()


@router.get("", response_model=list[GoalResponse])
def list_all(
    current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> list[GoalResponse]:
    return list_goals(db, current_user.id)


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create(
    data: GoalCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> GoalResponse:
    return create_goal(db, current_user.id, data)


@router.get("/{goal_id}", response_model=GoalResponse)
def get(
    goal_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> GoalResponse:
    return get_goal(db, current_user.id, goal_id)


@router.patch("/{goal_id}", response_model=GoalResponse)
def update(
    goal_id: UUID,
    data: GoalUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> GoalResponse:
    return update_goal(db, current_user.id, goal_id, data)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    goal_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    delete_goal(db, current_user.id, goal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
