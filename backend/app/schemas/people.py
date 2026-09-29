from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import IOUAdjustmentDirection, IOUEventType


class PersonCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be blank")
        return cleaned


class PersonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("name must not be blank")
        return value.strip()


class IOUEventCreate(BaseModel):
    event_type: IOUEventType
    amount_cad: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    date: date_type
    adjustment_direction: IOUAdjustmentDirection | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_adjustment_direction(self) -> "IOUEventCreate":
        if self.event_type == IOUEventType.ADJUSTMENT:
            if self.adjustment_direction is None:
                raise ValueError("adjustment_direction is required for adjustments")
        elif self.adjustment_direction is not None:
            raise ValueError("adjustment_direction is only valid for adjustments")
        return self


class IOUEventUpdate(BaseModel):
    event_type: IOUEventType | None = None
    amount_cad: Decimal | None = Field(
        default=None, gt=0, max_digits=14, decimal_places=2
    )
    date: date_type | None = None
    adjustment_direction: IOUAdjustmentDirection | None = None
    notes: str | None = None


class IOUEventResponse(IOUEventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    person_id: UUID
    effect_cad: Decimal
    running_balance_cad: Decimal
    created_at: datetime
    updated_at: datetime


class PersonSummary(BaseModel):
    id: UUID
    name: str
    direction: Literal["owed_to_user", "user_owes", "settled"]
    outstanding_amount_cad: Decimal
    last_activity: date_type | None
    event_count: int


class PersonDetail(PersonSummary):
    notes: str | None
    created_at: datetime
    updated_at: datetime
    events: list[IOUEventResponse]


class IOUTotals(BaseModel):
    owed_to_user_cad: Decimal
    user_owes_cad: Decimal
