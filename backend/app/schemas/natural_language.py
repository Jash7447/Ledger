from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import TransactionType
from app.schemas.financial import TransactionCreate


class NaturalLanguageTransactionRequest(BaseModel):
    text: str = Field(min_length=3, max_length=500)


class NaturalLanguageTransactionProposal(BaseModel):
    source_text: str
    type: TransactionType | None
    amount_cad: Decimal | None
    date: date
    description: str
    account_id: UUID | None
    account_name: str | None
    bucket_id: UUID | None
    bucket_name: str | None
    category_id: UUID | None
    category_name: str | None
    is_major_purchase: bool
    ready_to_confirm: bool
    warnings: list[str]
    errors: list[str]


class NaturalLanguageTransactionConfirm(BaseModel):
    source_text: str = Field(min_length=3, max_length=500)
    transaction: TransactionCreate


class NaturalLanguageQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class NaturalLanguageQueryResponse(BaseModel):
    intent: str
    answer: str
    amount_cad: Decimal | None = None
    count: int | None = None
    structured_data: dict[str, object]
