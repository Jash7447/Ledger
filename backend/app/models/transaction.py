from datetime import date as date_type
from datetime import datetime
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
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ExpenseClassification, TransactionType


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "user_id"],
            ["accounts.id", "accounts.user_id"],
            name="fk_transactions_account_owner",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["destination_account_id", "user_id"],
            ["accounts.id", "accounts.user_id"],
            name="fk_transactions_destination_account_owner",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["bucket_id", "user_id"],
            ["buckets.id", "buckets.user_id"],
            name="fk_transactions_bucket_owner",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["category_id", "user_id"],
            ["categories.id", "categories.user_id"],
            name="fk_transactions_category_owner",
            ondelete="RESTRICT",
        ),
        CheckConstraint("amount_cad > 0", name="ck_transactions_positive_amount"),
        CheckConstraint(
            "(type = 'transfer' AND destination_account_id IS NOT NULL) OR "
            "(type <> 'transfer' AND destination_account_id IS NULL)",
            name="ck_transactions_transfer_destination",
        ),
        CheckConstraint(
            "destination_account_id IS NULL OR destination_account_id <> account_id",
            name="ck_transactions_distinct_transfer_accounts",
        ),
        CheckConstraint(
            "type <> 'transfer' OR (bucket_id IS NULL AND category_id IS NULL)",
            name="ck_transactions_transfer_uncategorized",
        ),
        CheckConstraint(
            "type = 'expense' OR expense_classification IS NULL",
            name="ck_transactions_expense_classification",
        ),
        CheckConstraint(
            "type = 'expense' OR is_major_purchase = false",
            name="ck_transactions_major_purchase_expense",
        ),
        Index("ix_transactions_user_date", "user_id", "date"),
        Index("ix_transactions_user_account_date", "user_id", "account_id", "date"),
        Index("ix_transactions_user_type_date", "user_id", "type", "date"),
        Index("ix_transactions_user_category_date", "user_id", "category_id", "date"),
        Index("ix_transactions_user_major_date", "user_id", "is_major_purchase", "date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(Uuid)
    destination_account_id: Mapped[UUID | None] = mapped_column(Uuid)
    type: Mapped[TransactionType] = mapped_column(
        Enum(
            TransactionType,
            name="transaction_type",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda values: [item.value for item in values],
        )
    )
    amount_cad: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    date: Mapped[date_type] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String(255))
    bucket_id: Mapped[UUID | None] = mapped_column(Uuid)
    category_id: Mapped[UUID | None] = mapped_column(Uuid)
    notes: Mapped[str | None] = mapped_column(Text)
    expense_classification: Mapped[ExpenseClassification | None] = mapped_column(
        Enum(
            ExpenseClassification,
            name="expense_classification",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda values: [item.value for item in values],
        )
    )
    is_major_purchase: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
