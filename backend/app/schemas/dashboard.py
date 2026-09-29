from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.budget import BudgetProgress
from app.schemas.financial import TransactionResponse
from app.schemas.goal import GoalResponse


class DashboardSummary(BaseModel):
    current_balance_cad: Decimal
    monthly_income_cad: Decimal
    monthly_expenses_cad: Decimal
    monthly_savings_cad: Decimal
    education_spending_cad: Decimal
    money_owed_to_user_cad: Decimal
    money_owed_to_others_cad: Decimal


class SpendingBreakdownItem(BaseModel):
    id: UUID | None
    name: str
    amount_cad: Decimal


class DashboardResponse(BaseModel):
    period_start: date
    period_end: date
    summary: DashboardSummary
    spending_by_bucket: list[SpendingBreakdownItem]
    spending_by_category: list[SpendingBreakdownItem]
    budget_progress: list[BudgetProgress]
    recent_transactions: list[TransactionResponse]
    major_purchases: list[TransactionResponse]
    goals: list[GoalResponse]
