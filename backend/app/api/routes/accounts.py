from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.models.account import Account
from app.schemas.financial import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    AccountWithBalance,
)
from app.services.accounts import (
    archive_account,
    create_account,
    get_account_with_balance,
    list_accounts_with_balances,
    update_account,
)

router = APIRouter()


def serialize_account(account: Account, balance: Decimal) -> AccountWithBalance:
    account_data = AccountResponse.model_validate(account).model_dump()
    return AccountWithBalance(**account_data, balance_cad=balance)


@router.get("", response_model=list[AccountWithBalance])
def list_accounts(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    include_archived: Annotated[bool, Query()] = False,
) -> list[AccountWithBalance]:
    return [
        serialize_account(account, balance)
        for account, balance in list_accounts_with_balances(
            db, current_user.id, include_archived
        )
    ]


@router.post("", response_model=AccountWithBalance, status_code=status.HTTP_201_CREATED)
def create(
    data: AccountCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AccountWithBalance:
    account = create_account(db, current_user.id, data)
    return serialize_account(account, Decimal("0.00"))


@router.get("/{account_id}", response_model=AccountWithBalance)
def get(
    account_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AccountWithBalance:
    account, balance = get_account_with_balance(db, current_user.id, account_id)
    return serialize_account(account, balance)


@router.patch("/{account_id}", response_model=AccountWithBalance)
def update(
    account_id: UUID,
    data: AccountUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AccountWithBalance:
    update_account(db, current_user.id, account_id, data)
    account, balance = get_account_with_balance(db, current_user.id, account_id)
    return serialize_account(account, balance)


@router.post("/{account_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive(
    account_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    archive_account(db, current_user.id, account_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
