from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import IOUAdjustmentDirection, IOUEventType


class IOUEvent(Base):
    __tablename__ = "iou_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["person_id", "user_id"],
            ["people.id", "people.user_id"],
            name="fk_iou_events_person_owner",
            ondelete="CASCADE",
        ),
        CheckConstraint("amount_cad > 0", name="ck_iou_events_positive_amount"),
        CheckConstraint(
            "(event_type = 'adjustment' AND adjustment_direction IS NOT NULL) OR "
            "(event_type <> 'adjustment' AND adjustment_direction IS NULL)",
            name="ck_iou_events_adjustment_direction",
        ),
        Index("ix_iou_events_user_person_date", "user_id", "person_id", "date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    person_id: Mapped[UUID] = mapped_column(Uuid)
    event_type: Mapped[IOUEventType] = mapped_column(
        Enum(
            IOUEventType,
            name="iou_event_type",
            native_enum=False,
            create_constraint=True,
            length=24,
            values_callable=lambda values: [item.value for item in values],
        )
    )
    adjustment_direction: Mapped[IOUAdjustmentDirection | None] = mapped_column(
        Enum(
            IOUAdjustmentDirection,
            name="iou_adjustment_direction",
            native_enum=False,
            create_constraint=True,
            length=16,
            values_callable=lambda values: [item.value for item in values],
        )
    )
    amount_cad: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    date: Mapped[date_type] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
