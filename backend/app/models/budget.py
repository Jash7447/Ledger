from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        ForeignKeyConstraint(
            ["bucket_id", "user_id"],
            ["buckets.id", "buckets.user_id"],
            name="fk_budgets_bucket_owner",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["category_id", "user_id"],
            ["categories.id", "categories.user_id"],
            name="fk_budgets_category_owner",
            ondelete="RESTRICT",
        ),
        CheckConstraint("amount_cad > 0", name="ck_budgets_positive_amount"),
        CheckConstraint("period_end >= period_start", name="ck_budgets_valid_period"),
        CheckConstraint(
            "(bucket_id IS NOT NULL AND category_id IS NULL) OR "
            "(bucket_id IS NULL AND category_id IS NOT NULL)",
            name="ck_budgets_single_scope",
        ),
        UniqueConstraint(
            "user_id", "bucket_id", "period_start", name="uq_budgets_user_bucket_period"
        ),
        UniqueConstraint(
            "user_id",
            "category_id",
            "period_start",
            name="uq_budgets_user_category_period",
        ),
        Index("ix_budgets_user_period", "user_id", "period_start"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    bucket_id: Mapped[UUID | None] = mapped_column(Uuid)
    category_id: Mapped[UUID | None] = mapped_column(Uuid)
    amount_cad: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
