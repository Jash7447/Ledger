from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import DisplayCurrency


class CurrencySetting(Base):
    __tablename__ = "currency_settings"
    __table_args__ = (
        CheckConstraint("cad_to_inr_rate > 0", name="ck_currency_settings_positive_rate"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    display_currency: Mapped[DisplayCurrency] = mapped_column(
        Enum(
            DisplayCurrency,
            name="display_currency",
            native_enum=False,
            create_constraint=True,
            length=3,
            values_callable=lambda values: [item.value for item in values],
        ),
        default=DisplayCurrency.CAD,
        server_default=DisplayCurrency.CAD.value,
    )
    cad_to_inr_rate: Mapped[Decimal] = mapped_column(
        Numeric(14, 4), default=Decimal("70.0000"), server_default="70.0000"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
