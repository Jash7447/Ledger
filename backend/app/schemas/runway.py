from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class RunwayEstimate(BaseModel):
    is_enabled: bool
    lookback_months: int
    period_start: date
    period_end: date
    available_funds_cad: Decimal
    average_monthly_spending_cad: Decimal
    estimated_months: Decimal | None
