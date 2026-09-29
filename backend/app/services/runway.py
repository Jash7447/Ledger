from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.runway import RunwayEstimate
from app.services.accounts import list_accounts_with_balances
from app.services.settings import get_runway_settings

ZERO = Decimal("0.00")


def get_runway_estimate(
    db: Session, user_id: UUID, as_of: date | None = None
) -> RunwayEstimate:
    settings = get_runway_settings(db, user_id)
    today = as_of or date.today()
    current_month = today.replace(day=1)
    period_start = _subtract_months(current_month, settings.lookback_months)
    period_end = current_month - timedelta(days=1)
    total_spending = Decimal(
        db.scalar(
            select(func.coalesce(func.sum(Transaction.amount_cad), ZERO)).where(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.date >= period_start,
                Transaction.date < current_month,
            )
        )
        or ZERO
    )
    average = (total_spending / Decimal(settings.lookback_months)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    available = sum(
        (balance for _, balance in list_accounts_with_balances(db, user_id)), ZERO
    )
    estimated = None
    if settings.is_enabled and available > 0 and average > 0:
        estimated = (available / average).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
    return RunwayEstimate(
        is_enabled=settings.is_enabled,
        lookback_months=settings.lookback_months,
        period_start=period_start,
        period_end=period_end,
        available_funds_cad=available,
        average_monthly_spending_cad=average,
        estimated_months=estimated,
    )


def _subtract_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 - months
    year, zero_based_month = divmod(month_index, 12)
    return date(year, zero_based_month + 1, 1)
