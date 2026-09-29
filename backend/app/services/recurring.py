from calendar import monthrange
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import FinancialReferenceError, ResourceNotFoundError
from app.models.account import Account
from app.models.bucket import Bucket
from app.models.category import Category
from app.models.enums import CategoryKind, RecurringFrequency
from app.models.recurring_transaction import RecurringTransaction
from app.schemas.recurring import RecurringCreate, RecurringResponse, RecurringUpdate


def list_recurring(
    db: Session, user_id: UUID, is_active: bool | None = None
) -> list[RecurringResponse]:
    statement = (
        select(RecurringTransaction)
        .where(RecurringTransaction.user_id == user_id)
        .order_by(
            RecurringTransaction.is_active.desc(),
            RecurringTransaction.start_date,
            RecurringTransaction.description,
        )
    )
    if is_active is not None:
        statement = statement.where(RecurringTransaction.is_active == is_active)
    return _serialize_many(db, user_id, list(db.scalars(statement).all()))


def get_recurring(db: Session, user_id: UUID, recurring_id: UUID) -> RecurringResponse:
    recurring = _get_recurring(db, user_id, recurring_id)
    return _serialize_many(db, user_id, [recurring])[0]


def create_recurring(
    db: Session, user_id: UUID, data: RecurringCreate
) -> RecurringResponse:
    account, category = _validate_references(db, user_id, data.account_id, data.category_id)
    recurring = RecurringTransaction(
        user_id=user_id,
        bucket_id=category.bucket_id,
        **data.model_dump(),
    )
    db.add(recurring)
    db.commit()
    db.refresh(recurring)
    return _serialize_many(
        db, user_id, [recurring], accounts={account.id: account.name}
    )[0]


def update_recurring(
    db: Session,
    user_id: UUID,
    recurring_id: UUID,
    data: RecurringUpdate,
) -> RecurringResponse:
    recurring = _get_recurring(db, user_id, recurring_id)
    current = RecurringCreate(
        account_id=recurring.account_id,
        category_id=recurring.category_id,
        description=recurring.description,
        expected_amount_cad=recurring.expected_amount_cad,
        frequency=recurring.frequency,
        start_date=recurring.start_date,
        end_date=recurring.end_date,
        is_active=recurring.is_active,
        notes=recurring.notes,
    ).model_dump()
    current.update(data.model_dump(exclude_unset=True))
    merged = RecurringCreate.model_validate(current)
    account, category = _validate_references(
        db,
        user_id,
        merged.account_id,
        merged.category_id,
        allow_inactive_account_id=recurring.account_id,
    )
    for field, value in merged.model_dump().items():
        setattr(recurring, field, value)
    assert category.bucket_id is not None
    recurring.bucket_id = category.bucket_id
    db.commit()
    db.refresh(recurring)
    return _serialize_many(
        db, user_id, [recurring], accounts={account.id: account.name}
    )[0]


def delete_recurring(db: Session, user_id: UUID, recurring_id: UUID) -> None:
    recurring = _get_recurring(db, user_id, recurring_id)
    db.delete(recurring)
    db.commit()


def _get_recurring(db: Session, user_id: UUID, recurring_id: UUID) -> RecurringTransaction:
    recurring = db.scalar(
        select(RecurringTransaction).where(
            RecurringTransaction.id == recurring_id,
            RecurringTransaction.user_id == user_id,
        )
    )
    if recurring is None:
        raise ResourceNotFoundError("Recurring transaction")
    return recurring


def _validate_references(
    db: Session,
    user_id: UUID,
    account_id: UUID,
    category_id: UUID,
    allow_inactive_account_id: UUID | None = None,
) -> tuple[Account, Category]:
    account = db.scalar(
        select(Account).where(Account.id == account_id, Account.user_id == user_id)
    )
    if account is None or (
        not account.is_active and account.id != allow_inactive_account_id
    ):
        raise FinancialReferenceError(
            "Recurring account must be active and owned by the authenticated user"
        )
    category = db.scalar(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    )
    if category is None or category.kind != CategoryKind.EXPENSE:
        raise FinancialReferenceError(
            "Recurring category must be an expense category owned by the authenticated user"
        )
    assert category.bucket_id is not None
    return account, category


def _serialize_many(
    db: Session,
    user_id: UUID,
    items: list[RecurringTransaction],
    accounts: dict[UUID, str] | None = None,
) -> list[RecurringResponse]:
    if not items:
        return []
    account_names = accounts or {
        item_id: name
        for item_id, name in db.execute(
            select(Account.id, Account.name).where(
                Account.user_id == user_id,
                Account.id.in_({item.account_id for item in items}),
            )
        )
    }
    bucket_names = {
        item_id: name
        for item_id, name in db.execute(
            select(Bucket.id, Bucket.name).where(
                Bucket.user_id == user_id,
                Bucket.id.in_({item.bucket_id for item in items}),
            )
        )
    }
    category_names = {
        item_id: name
        for item_id, name in db.execute(
            select(Category.id, Category.name).where(
                Category.user_id == user_id,
                Category.id.in_({item.category_id for item in items}),
            )
        )
    }
    today = date.today()
    return [
        RecurringResponse(
            **RecurringCreate.model_validate(item).model_dump(),
            id=item.id,
            bucket_id=item.bucket_id,
            account_name=account_names.get(item.account_id, "Unknown"),
            bucket_name=bucket_names.get(item.bucket_id, "Unknown"),
            category_name=category_names.get(item.category_id, "Unknown"),
            next_occurrence_date=_next_occurrence(item, today),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in items
    ]


def _next_occurrence(item: RecurringTransaction, as_of: date) -> date | None:
    if not item.is_active:
        return None
    if item.frequency in {RecurringFrequency.WEEKLY, RecurringFrequency.BIWEEKLY}:
        interval = 7 if item.frequency == RecurringFrequency.WEEKLY else 14
        elapsed = max(0, (as_of - item.start_date).days)
        steps = (elapsed + interval - 1) // interval
        candidate = item.start_date + timedelta(days=steps * interval)
    else:
        interval_months = {
            RecurringFrequency.MONTHLY: 1,
            RecurringFrequency.QUARTERLY: 3,
            RecurringFrequency.YEARLY: 12,
        }[item.frequency]
        elapsed_months = max(
            0,
            (as_of.year - item.start_date.year) * 12 + as_of.month - item.start_date.month,
        )
        steps = elapsed_months // interval_months
        candidate = _add_months(item.start_date, steps * interval_months)
        if candidate < as_of:
            candidate = _add_months(item.start_date, (steps + 1) * interval_months)
    if item.end_date is not None and candidate > item.end_date:
        return None
    return candidate


def _add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)
