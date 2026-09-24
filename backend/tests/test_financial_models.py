from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import FinancialReferenceError
from app.models.account import Account
from app.models.bucket import Bucket
from app.models.category import Category
from app.models.enums import AccountType, CategoryKind, TransactionType
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.financial import CategoryCreate, TransactionCreate
from app.services.financial_validation import validate_transaction_references


def create_user(client: TestClient, email: str) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "display_name": email.split("@")[0],
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    return response.json()["user"]


def test_signup_initializes_default_buckets_and_categories(
    client: TestClient, db_session: Session
) -> None:
    user_payload = create_user(client, "catalog@example.com")
    user_id = UUID(str(user_payload["id"]))

    bucket_count = db_session.scalar(
        select(func.count()).select_from(Bucket).where(Bucket.user_id == user_id)
    )
    expense_count = db_session.scalar(
        select(func.count())
        .select_from(Category)
        .where(Category.user_id == user_id, Category.kind == CategoryKind.EXPENSE)
    )
    income_count = db_session.scalar(
        select(func.count())
        .select_from(Category)
        .where(Category.user_id == user_id, Category.kind == CategoryKind.INCOME)
    )
    funding_count = db_session.scalar(
        select(func.count())
        .select_from(Category)
        .where(Category.user_id == user_id, Category.kind == CategoryKind.FUNDING)
    )

    assert bucket_count == 7
    assert expense_count == 41
    assert income_count == 6
    assert funding_count == 4


def test_transaction_schemas_enforce_type_specific_rules() -> None:
    source_id = uuid4()
    destination_id = uuid4()
    transfer = TransactionCreate(
        account_id=source_id,
        destination_account_id=destination_id,
        type=TransactionType.TRANSFER,
        amount_cad=Decimal("10.25"),
        date=date.today(),
        description="Move to savings",
    )
    assert transfer.amount_cad == Decimal("10.25")

    with pytest.raises(ValidationError):
        TransactionCreate(
            account_id=source_id,
            type=TransactionType.TRANSFER,
            amount_cad=Decimal("10.00"),
            date=date.today(),
            description="Missing destination",
        )

    with pytest.raises(ValidationError):
        CategoryCreate(name="Salary", kind=CategoryKind.INCOME, bucket_id=uuid4())


def test_service_and_database_reject_cross_user_references(
    client: TestClient, db_session: Session
) -> None:
    first = create_user(client, "first-owner@example.com")
    second = create_user(client, "second-owner@example.com")
    first_user = db_session.get(User, UUID(str(first["id"])))
    second_user = db_session.get(User, UUID(str(second["id"])))
    assert first_user is not None and second_user is not None

    first_account = Account(
        user_id=first_user.id, name="First chequing", type=AccountType.CHEQUING
    )
    second_account = Account(
        user_id=second_user.id, name="Second chequing", type=AccountType.CHEQUING
    )
    db_session.add_all([first_account, second_account])
    db_session.commit()

    data = TransactionCreate(
        account_id=second_account.id,
        type=TransactionType.INCOME,
        amount_cad=Decimal("100.00"),
        date=date.today(),
        description="Invalid owner",
    )
    with pytest.raises(FinancialReferenceError):
        validate_transaction_references(db_session, first_user.id, data)

    db_session.add(
        Transaction(
            user_id=first_user.id,
            account_id=second_account.id,
            type=TransactionType.INCOME,
            amount_cad=Decimal("100.00"),
            date=date.today(),
            description="Bypass attempt",
            is_major_purchase=False,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_money_is_persisted_as_decimal(client: TestClient, db_session: Session) -> None:
    payload = create_user(client, "decimal@example.com")
    user = db_session.get(User, UUID(str(payload["id"])))
    assert user is not None
    account = Account(user_id=user.id, name="Cash", type=AccountType.CASH)
    db_session.add(account)
    db_session.flush()
    transaction = Transaction(
        user_id=user.id,
        account_id=account.id,
        type=TransactionType.EXPENSE,
        amount_cad=Decimal("42.50"),
        date=date.today(),
        description="Books",
        is_major_purchase=False,
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    assert transaction.amount_cad == Decimal("42.50")
