from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Uuid, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RunwaySetting(Base):
    __tablename__ = "runway_settings"
    __table_args__ = (
        CheckConstraint(
            "lookback_months >= 1 AND lookback_months <= 24",
            name="ck_runway_settings_lookback_range",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    lookback_months: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
