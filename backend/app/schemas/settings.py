from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DisplayCurrency


class CurrencySettingsUpdate(BaseModel):
    display_currency: DisplayCurrency | None = None
    cad_to_inr_rate: Decimal | None = Field(
        default=None, gt=0, max_digits=14, decimal_places=4
    )


class CurrencySettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_currency: DisplayCurrency
    cad_to_inr_rate: Decimal
    updated_at: datetime


class RunwaySettingsUpdate(BaseModel):
    is_enabled: bool | None = None
    lookback_months: int | None = Field(default=None, ge=1, le=24)


class RunwaySettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_enabled: bool
    lookback_months: int
    updated_at: datetime
