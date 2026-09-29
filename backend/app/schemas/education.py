from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.financial import TransactionResponse


class EducationCategoryTotal(BaseModel):
    category_id: UUID
    category_name: str
    amount_cad: Decimal


class EducationReport(BaseModel):
    date_from: date
    date_to: date
    total_spent_cad: Decimal
    transaction_count: int
    spending_by_category: list[EducationCategoryTotal]
    transactions: list[TransactionResponse]
