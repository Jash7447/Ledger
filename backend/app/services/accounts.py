from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.exceptions import (
    FinancialReferenceError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.models.account import Account
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.financial import AccountCreate, AccountUpdate


def _balance_expression() -> ColumnElement[Decimal]:
    return func.coalesce(
        func.sum(
            case(
                (
                    and_(
                        Transaction.type == TransactionType.INCOME,
                        Transaction.account_id == Account.id,
                    ),
                    Transaction.amount_cad,
                ),
                (
                    and_(
                        Transaction.type == TransactionType.EXPENSE,
                        Transaction.account_id == Account.id,
                    ),
                    -Transaction.amount_cad,
                ),
                (
                    and_(
                        Transaction.type == TransactionType.TRANSFER,
                        Transaction.account_id == Account.id,
                    ),
                    -Transaction.amount_cad,
                ),
                (
                    and_(
                        Transaction.type == TransactionType.TRANSFER,
                        Transaction.destination_account_id == Account.id,
                    ),
                    Transaction.amount_cad,
                ),
                else_=Decimal("0.00"),
            )
        ),
        Decimal("0.00"),
    )


def list_accounts_with_balances(
    db: Session, user_id: UUID, include_archived: bool = False
) -> list[tuple[Account, Decimal]]:
    balance = _balance_expression()
    statement = (
        select(Account, balance)
        .outerjoin(
            Transaction,
            and_(
                Transaction.user_id == Account.user_id,
                or_(
                    Transaction.account_id == Account.id,
                    Transaction.destination_account_id == Account.id,
                ),
            ),
        )
        .where(Account.user_id == user_id)
        .group_by(Account.id)
        .order_by(Account.is_active.desc(), Account.created_at, Account.name)
    )
    if not include_archived:
        statement = statement.where(Account.is_active.is_(True))
    return [(account, Decimal(balance_value)) for account, balance_value in db.execute(statement)]


def get_account_with_balance(
    db: Session, user_id: UUID, account_id: UUID
) -> tuple[Account, Decimal]:
    balance = _balance_expression()
    row = db.execute(
        select(Account, balance)
        .outerjoin(
            Transaction,
            and_(
                Transaction.user_id == Account.user_id,
                or_(
                    Transaction.account_id == Account.id,
                    Transaction.destination_account_id == Account.id,
                ),
            ),
        )
        .where(Account.user_id == user_id, Account.id == account_id)
        .group_by(Account.id)
    ).one_or_none()
    if row is None:
        raise ResourceNotFoundError("Account")
    return row[0], Decimal(row[1])


def create_account(db: Session, user_id: UUID, data: AccountCreate) -> Account:
    if data.currency != "CAD":
        raise FinancialReferenceError("Only CAD accounts are supported currently")
    account = Account(
        user_id=user_id,
        name=data.name.strip(),
        type=data.type,
        currency=data.currency,
    )
    db.add(account)
    _commit_account(db)
    db.refresh(account)
    return account


def update_account(
    db: Session, user_id: UUID, account_id: UUID, data: AccountUpdate
) -> Account:
    account = db.scalar(
        select(Account).where(Account.id == account_id, Account.user_id == user_id)
    )
    if account is None:
        raise ResourceNotFoundError("Account")
    changes = data.model_dump(exclude_unset=True)
    if changes.get("name") is not None:
        changes["name"] = changes["name"].strip()
    for field, value in changes.items():
        if value is not None:
            setattr(account, field, value)
    _commit_account(db)
    db.refresh(account)
    return account


def archive_account(db: Session, user_id: UUID, account_id: UUID) -> None:
    account = db.scalar(
        select(Account).where(Account.id == account_id, Account.user_id == user_id)
    )
    if account is None:
        raise ResourceNotFoundError("Account")
    account.is_active = False
    db.commit()


def _commit_account(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ResourceConflictError("An account with this name already exists") from error
