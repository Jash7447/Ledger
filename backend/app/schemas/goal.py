from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import GoalStatus


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    target_amount_cad: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    current_amount_cad: Decimal = Field(
        default=Decimal("0.00"), ge=0, max_digits=14, decimal_places=2
    )
    target_date: date | None = None
    status: GoalStatus = GoalStatus.ACTIVE

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be blank")
        return cleaned


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    target_amount_cad: Decimal | None = Field(
        default=None, gt=0, max_digits=14, decimal_places=2
    )
    current_amount_cad: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    target_date: date | None = None
    status: GoalStatus | None = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("name must not be blank")
        return value.strip()


class GoalResponse(GoalCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    remaining_amount_cad: Decimal
    percentage_complete: Decimal
    created_at: datetime
    updated_at: datetime
