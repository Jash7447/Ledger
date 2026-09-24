from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.models.transaction import Transaction
from app.schemas.financial import (
    TransactionCreate,
    TransactionListQuery,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.transactions import (
    create_transaction,
    delete_transaction,
    get_transaction,
    list_transactions,
    update_transaction,
)

router = APIRouter()


@router.get("", response_model=TransactionListResponse)
def list_all(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    query: Annotated[TransactionListQuery, Query()],
) -> TransactionListResponse:
    items, total = list_transactions(db, current_user.id, query)
    return TransactionListResponse(
        items=[TransactionResponse.model_validate(item) for item in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
        pages=max(1, (total + query.page_size - 1) // query.page_size),
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create(
    data: TransactionCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Transaction:
    return create_transaction(db, current_user.id, data)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get(
    transaction_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Transaction:
    return get_transaction(db, current_user.id, transaction_id)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update(
    transaction_id: UUID,
    data: TransactionUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Transaction:
    return update_transaction(db, current_user.id, transaction_id, data)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    transaction_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    delete_transaction(db, current_user.id, transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
