from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import FinancialReferenceError
from app.models.account import Account
from app.models.bucket import Bucket
from app.models.category import Category
from app.models.enums import CategoryKind, TransactionType
from app.schemas.financial import TransactionCreate


def validate_transaction_references(
    db: Session,
    user_id: UUID,
    data: TransactionCreate,
    allow_inactive_account_ids: set[UUID] | None = None,
) -> None:
    allowed_inactive = allow_inactive_account_ids or set()
    account = db.scalar(
        select(Account).where(Account.id == data.account_id, Account.user_id == user_id)
    )
    if account is None or (not account.is_active and account.id not in allowed_inactive):
        raise FinancialReferenceError("Account does not belong to the authenticated user")

    if data.destination_account_id is not None:
        destination = db.scalar(
            select(Account).where(
                Account.id == data.destination_account_id,
                Account.user_id == user_id,
            )
        )
        if destination is None or (
            not destination.is_active and destination.id not in allowed_inactive
        ):
            raise FinancialReferenceError(
                "Destination account does not belong to the authenticated user"
            )

    bucket = None
    if data.bucket_id is not None:
        bucket = db.scalar(
            select(Bucket).where(Bucket.id == data.bucket_id, Bucket.user_id == user_id)
        )
        if bucket is None:
            raise FinancialReferenceError("Bucket does not belong to the authenticated user")

    if data.category_id is None:
        return
    category = db.scalar(
        select(Category).where(Category.id == data.category_id, Category.user_id == user_id)
    )
    if category is None:
        raise FinancialReferenceError("Category does not belong to the authenticated user")

    if data.type == TransactionType.EXPENSE:
        if category.kind != CategoryKind.EXPENSE or category.bucket_id != data.bucket_id:
            raise FinancialReferenceError("Expense category does not match the selected bucket")
    elif data.type == TransactionType.INCOME and category.kind not in {
        CategoryKind.INCOME,
        CategoryKind.FUNDING,
    }:
        raise FinancialReferenceError("Income requires an income or funding category")
