from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class BudgetCreate(BaseModel):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    amount_cad: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    bucket_id: UUID | None = None
    category_id: UUID | None = None

    @field_validator("month")
    @classmethod
    def validate_month_year(cls, value: str) -> str:
        if value.startswith("0000"):
            raise ValueError("Month year must be greater than zero")
        return value

    @model_validator(mode="after")
    def validate_scope(self) -> "BudgetCreate":
        if (self.bucket_id is None) == (self.category_id is None):
            raise ValueError("A budget must target exactly one bucket or category")
        return self


class BudgetUpdate(BaseModel):
    month: str | None = Field(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    amount_cad: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    bucket_id: UUID | None = None
    category_id: UUID | None = None

    @field_validator("month")
    @classmethod
    def validate_month_year(cls, value: str | None) -> str | None:
        if value is not None and value.startswith("0000"):
            raise ValueError("Month year must be greater than zero")
        return value


class BudgetProgress(BaseModel):
    id: UUID
    bucket_id: UUID | None
    category_id: UUID | None
    scope_type: Literal["bucket", "category"]
    scope_name: str
    amount_cad: Decimal
    period_start: date
    period_end: date
    spent_cad: Decimal
    remaining_cad: Decimal
    percentage_used: Decimal
    is_over_budget: bool
    created_at: datetime
    updated_at: datetime
