from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.models.transaction import Transaction
from app.schemas.financial import TransactionResponse
from app.schemas.natural_language import (
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
    NaturalLanguageTransactionConfirm,
    NaturalLanguageTransactionProposal,
    NaturalLanguageTransactionRequest,
)
from app.services.natural_language_queries import answer_financial_query
from app.services.natural_language_transactions import propose_transaction
from app.services.transactions import create_transaction

router = APIRouter()


@router.post("/query", response_model=NaturalLanguageQueryResponse)
def query(
    data: NaturalLanguageQueryRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> NaturalLanguageQueryResponse:
    return answer_financial_query(db, current_user.id, data.question)


@router.post("/transactions/propose", response_model=NaturalLanguageTransactionProposal)
def propose(
    data: NaturalLanguageTransactionRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> NaturalLanguageTransactionProposal:
    return propose_transaction(db, current_user.id, data.text)


@router.post(
    "/transactions/confirm",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirm(
    data: NaturalLanguageTransactionConfirm,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Transaction:
    return create_transaction(db, current_user.id, data.transaction)
