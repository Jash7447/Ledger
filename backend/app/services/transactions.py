from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError
from app.models.enums import SortDirection, TransactionSortField
from app.models.transaction import Transaction
from app.schemas.financial import TransactionCreate, TransactionListQuery, TransactionUpdate
from app.services.financial_validation import validate_transaction_references


def list_transactions(
    db: Session, user_id: UUID, query: TransactionListQuery
) -> tuple[list[Transaction], int]:
    filters = [Transaction.user_id == user_id]
    search = query.search.strip() if query.search else None
    if search:
        filters.append(
            or_(
                Transaction.description.icontains(search, autoescape=True),
                Transaction.notes.icontains(search, autoescape=True),
            )
        )
    if query.date_from is not None:
        filters.append(Transaction.date >= query.date_from)
    if query.date_to is not None:
        filters.append(Transaction.date <= query.date_to)
    if query.account_id is not None:
        filters.append(
            or_(
                Transaction.account_id == query.account_id,
                Transaction.destination_account_id == query.account_id,
            )
        )
    if query.bucket_id is not None:
        filters.append(Transaction.bucket_id == query.bucket_id)
    if query.category_id is not None:
        filters.append(Transaction.category_id == query.category_id)
    if query.type is not None:
        filters.append(Transaction.type == query.type)
    if query.is_major_purchase is not None:
        filters.append(Transaction.is_major_purchase == query.is_major_purchase)

    sort_column = {
        TransactionSortField.DATE: Transaction.date,
        TransactionSortField.AMOUNT: Transaction.amount_cad,
        TransactionSortField.DESCRIPTION: Transaction.description,
        TransactionSortField.CREATED_AT: Transaction.created_at,
    }[query.sort_by]
    order = sort_column.asc() if query.sort_direction == SortDirection.ASC else sort_column.desc()
    total = db.scalar(select(func.count()).select_from(Transaction).where(*filters)) or 0
    transactions = list(
        db.scalars(
            select(Transaction)
            .where(*filters)
            .order_by(order, Transaction.created_at.desc(), Transaction.id)
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        ).all()
    )
    return transactions, total


def get_transaction(db: Session, user_id: UUID, transaction_id: UUID) -> Transaction:
    transaction = db.scalar(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
    )
    if transaction is None:
        raise ResourceNotFoundError("Transaction")
    return transaction


def create_transaction(db: Session, user_id: UUID, data: TransactionCreate) -> Transaction:
    validate_transaction_references(db, user_id, data)
    transaction = Transaction(user_id=user_id, **data.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def update_transaction(
    db: Session,
    user_id: UUID,
    transaction_id: UUID,
    data: TransactionUpdate,
) -> Transaction:
    transaction = get_transaction(db, user_id, transaction_id)
    current = {
        "account_id": transaction.account_id,
        "destination_account_id": transaction.destination_account_id,
        "type": transaction.type,
        "amount_cad": transaction.amount_cad,
        "date": transaction.date,
        "description": transaction.description,
        "bucket_id": transaction.bucket_id,
        "category_id": transaction.category_id,
        "notes": transaction.notes,
        "expense_classification": transaction.expense_classification,
        "is_major_purchase": transaction.is_major_purchase,
    }
    current.update(data.model_dump(exclude_unset=True))
    merged = TransactionCreate.model_validate(current)
    existing_account_ids = {transaction.account_id}
    if transaction.destination_account_id is not None:
        existing_account_ids.add(transaction.destination_account_id)
    validate_transaction_references(
        db,
        user_id,
        merged,
        allow_inactive_account_ids=existing_account_ids,
    )
    for field, value in merged.model_dump().items():
        setattr(transaction, field, value)
    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, user_id: UUID, transaction_id: UUID) -> None:
    transaction = get_transaction(db, user_id, transaction_id)
    db.delete(transaction)
    db.commit()
