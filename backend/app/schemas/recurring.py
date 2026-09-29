from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import RecurringFrequency


class RecurringCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: UUID
    category_id: UUID
    description: str = Field(min_length=1, max_length=255)
    expected_amount_cad: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    frequency: RecurringFrequency
    start_date: date
    end_date: date | None = None
    is_active: bool = True
    notes: str | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "RecurringCreate":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class RecurringUpdate(BaseModel):
    account_id: UUID | None = None
    category_id: UUID | None = None
    description: str | None = Field(default=None, min_length=1, max_length=255)
    expected_amount_cad: Decimal | None = Field(
        default=None, gt=0, max_digits=14, decimal_places=2
    )
    frequency: RecurringFrequency | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None
    notes: str | None = None


class RecurringResponse(RecurringCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    bucket_id: UUID
    account_name: str
    bucket_name: str
    category_name: str
    next_occurrence_date: date | None
    created_at: datetime
    updated_at: datetime
