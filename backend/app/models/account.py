from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AccountType


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("currency = upper(currency)", name="ck_accounts_currency_uppercase"),
        CheckConstraint("length(currency) = 3", name="ck_accounts_currency_length"),
        UniqueConstraint("id", "user_id", name="uq_accounts_id_user_id"),
        UniqueConstraint("user_id", "name", name="uq_accounts_user_name"),
        Index("ix_accounts_user_active", "user_id", "is_active"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[AccountType] = mapped_column(
        Enum(
            AccountType,
            name="account_type",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda values: [item.value for item in values],
        )
    )
    currency: Mapped[str] = mapped_column(String(3), default="CAD", server_default="CAD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
