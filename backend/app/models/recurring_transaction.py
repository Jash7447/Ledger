from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import RecurringFrequency


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "user_id"],
            ["accounts.id", "accounts.user_id"],
            name="fk_recurring_account_owner",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["bucket_id", "user_id"],
            ["buckets.id", "buckets.user_id"],
            name="fk_recurring_bucket_owner",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["category_id", "user_id"],
            ["categories.id", "categories.user_id"],
            name="fk_recurring_category_owner",
            ondelete="RESTRICT",
        ),
        CheckConstraint("expected_amount_cad > 0", name="ck_recurring_positive_amount"),
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="ck_recurring_valid_dates",
        ),
        Index("ix_recurring_user_active", "user_id", "is_active"),
        Index("ix_recurring_user_account", "user_id", "account_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(Uuid)
    bucket_id: Mapped[UUID] = mapped_column(Uuid)
    category_id: Mapped[UUID] = mapped_column(Uuid)
    description: Mapped[str] = mapped_column(String(255))
    expected_amount_cad: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    frequency: Mapped[RecurringFrequency] = mapped_column(
        Enum(
            RecurringFrequency,
            name="recurring_frequency",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda values: [item.value for item in values],
        )
    )
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
