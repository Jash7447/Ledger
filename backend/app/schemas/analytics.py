from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.financial import TransactionResponse


class AnalyticsBreakdownItem(BaseModel):
    id: UUID | None = None
    name: str
    amount_cad: Decimal


class MonthlyAnalyticsItem(BaseModel):
    month: str
    income_cad: Decimal
    expenses_cad: Decimal
    savings_cad: Decimal


class AnalyticsSummary(BaseModel):
    income_cad: Decimal
    expenses_cad: Decimal
    savings_cad: Decimal
    education_spending_cad: Decimal
    major_purchase_spending_cad: Decimal


class AnalyticsResponse(BaseModel):
    date_from: date
    date_to: date
    summary: AnalyticsSummary
    spending_by_bucket: list[AnalyticsBreakdownItem]
    spending_by_category: list[AnalyticsBreakdownItem]
    fixed_vs_variable: list[AnalyticsBreakdownItem]
    monthly_trend: list[MonthlyAnalyticsItem]
    major_purchases: list[TransactionResponse]
