from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    FinancialReferenceError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.models.bucket import Bucket
from app.models.budget import Budget
from app.models.category import Category
from app.models.enums import CategoryKind, TransactionType
from app.models.transaction import Transaction
from app.schemas.budget import BudgetCreate, BudgetProgress, BudgetUpdate


def month_dates(month: str) -> tuple[date, date]:
    year, month_number = (int(part) for part in month.split("-"))
    start = date(year, month_number, 1)
    if month_number == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month_number + 1, 1)
    return start, next_month - timedelta(days=1)


def list_budgets_with_progress(
    db: Session, user_id: UUID, month: str
) -> list[BudgetProgress]:
    period_start, _ = month_dates(month)
    budgets = list(
        db.scalars(
            select(Budget)
            .where(Budget.user_id == user_id, Budget.period_start == period_start)
            .order_by(Budget.created_at, Budget.id)
        ).all()
    )
    return _progress_for_budgets(db, user_id, budgets)


def get_budget_with_progress(
    db: Session, user_id: UUID, budget_id: UUID
) -> BudgetProgress:
    budget = _get_budget(db, user_id, budget_id)
    return _progress_for_budgets(db, user_id, [budget])[0]


def create_budget(db: Session, user_id: UUID, data: BudgetCreate) -> BudgetProgress:
    _validate_scope(db, user_id, data.bucket_id, data.category_id)
    period_start, period_end = month_dates(data.month)
    budget = Budget(
        user_id=user_id,
        bucket_id=data.bucket_id,
        category_id=data.category_id,
        amount_cad=data.amount_cad,
        period_start=period_start,
        period_end=period_end,
    )
    db.add(budget)
    _commit_budget(db)
    db.refresh(budget)
    return _progress_for_budgets(db, user_id, [budget])[0]


def update_budget(
    db: Session, user_id: UUID, budget_id: UUID, data: BudgetUpdate
) -> BudgetProgress:
    budget = _get_budget(db, user_id, budget_id)
    changes = data.model_dump(exclude_unset=True)
    current = BudgetCreate(
        month=budget.period_start.strftime("%Y-%m"),
        amount_cad=budget.amount_cad,
        bucket_id=budget.bucket_id,
        category_id=budget.category_id,
    ).model_dump()
    current.update(changes)
    merged = BudgetCreate.model_validate(current)
    _validate_scope(db, user_id, merged.bucket_id, merged.category_id)
    period_start, period_end = month_dates(merged.month)
    budget.bucket_id = merged.bucket_id
    budget.category_id = merged.category_id
    budget.amount_cad = merged.amount_cad
    budget.period_start = period_start
    budget.period_end = period_end
    _commit_budget(db)
    db.refresh(budget)
    return _progress_for_budgets(db, user_id, [budget])[0]


def delete_budget(db: Session, user_id: UUID, budget_id: UUID) -> None:
    budget = _get_budget(db, user_id, budget_id)
    db.delete(budget)
    db.commit()


def _get_budget(db: Session, user_id: UUID, budget_id: UUID) -> Budget:
    budget = db.scalar(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    )
    if budget is None:
        raise ResourceNotFoundError("Budget")
    return budget


def _validate_scope(
    db: Session, user_id: UUID, bucket_id: UUID | None, category_id: UUID | None
) -> None:
    if bucket_id is not None:
        bucket = db.scalar(
            select(Bucket).where(Bucket.id == bucket_id, Bucket.user_id == user_id)
        )
        if bucket is None:
            raise FinancialReferenceError("Bucket does not belong to the authenticated user")
    if category_id is not None:
        category = db.scalar(
            select(Category).where(Category.id == category_id, Category.user_id == user_id)
        )
        if category is None or category.kind != CategoryKind.EXPENSE:
            raise FinancialReferenceError(
                "Budget category must be an expense category owned by the authenticated user"
            )


def _progress_for_budgets(
    db: Session, user_id: UUID, budgets: list[Budget]
) -> list[BudgetProgress]:
    if not budgets:
        return []
    period_starts = {budget.period_start for budget in budgets}
    period_ends = {budget.period_end for budget in budgets}
    start = min(period_starts)
    end = max(period_ends)
    bucket_spending = {
        bucket_id: Decimal(amount)
        for bucket_id, amount in db.execute(
            select(Transaction.bucket_id, func.sum(Transaction.amount_cad))
            .where(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.bucket_id.is_not(None),
            )
            .group_by(Transaction.bucket_id)
        )
    }
    category_spending = {
        category_id: Decimal(amount)
        for category_id, amount in db.execute(
            select(Transaction.category_id, func.sum(Transaction.amount_cad))
            .where(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.date >= start,
                Transaction.date <= end,
                Transaction.category_id.is_not(None),
            )
            .group_by(Transaction.category_id)
        )
    }
    bucket_names: dict[UUID, str] = {
        item_id: name
        for item_id, name in db.execute(
            select(Bucket.id, Bucket.name).where(
                Bucket.user_id == user_id,
                Bucket.id.in_([item.bucket_id for item in budgets if item.bucket_id]),
            )
        )
    }
    category_names: dict[UUID, str] = {
        item_id: name
        for item_id, name in db.execute(
            select(Category.id, Category.name).where(
                Category.user_id == user_id,
                Category.id.in_([item.category_id for item in budgets if item.category_id]),
            )
        )
    }
    results = []
    for budget in budgets:
        is_bucket = budget.bucket_id is not None
        scope_id = budget.bucket_id if is_bucket else budget.category_id
        assert scope_id is not None
        spending = bucket_spending if is_bucket else category_spending
        names = bucket_names if is_bucket else category_names
        spent = spending.get(scope_id, Decimal("0.00"))
        percentage = (spent / budget.amount_cad * Decimal("100")).quantize(Decimal("0.1"))
        results.append(
            BudgetProgress(
                id=budget.id,
                bucket_id=budget.bucket_id,
                category_id=budget.category_id,
                scope_type="bucket" if is_bucket else "category",
                scope_name=names.get(scope_id, "Unknown"),
                amount_cad=budget.amount_cad,
                period_start=budget.period_start,
                period_end=budget.period_end,
                spent_cad=spent,
                remaining_cad=budget.amount_cad - spent,
                percentage_used=percentage,
                is_over_budget=spent > budget.amount_cad,
                created_at=budget.created_at,
                updated_at=budget.updated_at,
            )
        )
    return results


def _commit_budget(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ResourceConflictError(
            "A budget already exists for this scope and month"
        ) from error
