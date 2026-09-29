from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceConflictError, ResourceNotFoundError
from app.models.enums import GoalStatus
from app.models.goal import Goal
from app.schemas.goal import GoalCreate, GoalResponse, GoalUpdate

ZERO = Decimal("0.00")


def list_goals(db: Session, user_id: UUID) -> list[GoalResponse]:
    goals = db.scalars(
        select(Goal)
        .where(Goal.user_id == user_id)
        .order_by(Goal.status, Goal.target_date.asc().nulls_last(), Goal.name)
    ).all()
    return [_serialize(goal) for goal in goals]


def get_goal(db: Session, user_id: UUID, goal_id: UUID) -> GoalResponse:
    return _serialize(_get_goal(db, user_id, goal_id))


def create_goal(db: Session, user_id: UUID, data: GoalCreate) -> GoalResponse:
    values = data.model_dump()
    values["status"] = _normalized_status(
        values["status"], values["current_amount_cad"], values["target_amount_cad"]
    )
    goal = Goal(user_id=user_id, **values)
    db.add(goal)
    _commit(db)
    db.refresh(goal)
    return _serialize(goal)


def update_goal(
    db: Session, user_id: UUID, goal_id: UUID, data: GoalUpdate
) -> GoalResponse:
    goal = _get_goal(db, user_id, goal_id)
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is not None or field == "target_date":
            setattr(goal, field, value)
    goal.status = _normalized_status(
        goal.status, goal.current_amount_cad, goal.target_amount_cad
    )
    _commit(db)
    db.refresh(goal)
    return _serialize(goal)


def delete_goal(db: Session, user_id: UUID, goal_id: UUID) -> None:
    db.delete(_get_goal(db, user_id, goal_id))
    db.commit()


def dashboard_goals(db: Session, user_id: UUID, limit: int = 4) -> list[GoalResponse]:
    goals = db.scalars(
        select(Goal)
        .where(Goal.user_id == user_id, Goal.status != GoalStatus.CANCELLED)
        .order_by(Goal.status, Goal.target_date.asc().nulls_last(), Goal.name)
        .limit(limit)
    ).all()
    return [_serialize(goal) for goal in goals]


def _get_goal(db: Session, user_id: UUID, goal_id: UUID) -> Goal:
    goal = db.scalar(select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id))
    if goal is None:
        raise ResourceNotFoundError("Goal")
    return goal


def _serialize(goal: Goal) -> GoalResponse:
    remaining = max(goal.target_amount_cad - goal.current_amount_cad, ZERO)
    percentage = (
        goal.current_amount_cad / goal.target_amount_cad * Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return GoalResponse(
        id=goal.id,
        name=goal.name,
        target_amount_cad=goal.target_amount_cad,
        current_amount_cad=goal.current_amount_cad,
        remaining_amount_cad=remaining,
        percentage_complete=percentage,
        target_date=goal.target_date,
        status=goal.status,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


def _normalized_status(
    status: GoalStatus, current: Decimal, target: Decimal
) -> GoalStatus:
    if status in {GoalStatus.PAUSED, GoalStatus.CANCELLED}:
        return status
    return GoalStatus.COMPLETED if current >= target else GoalStatus.ACTIVE


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ResourceConflictError("A goal with this name already exists") from error
