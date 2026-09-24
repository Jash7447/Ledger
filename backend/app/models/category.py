from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import CategoryKind


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        ForeignKeyConstraint(
            ["bucket_id", "user_id"],
            ["buckets.id", "buckets.user_id"],
            name="fk_categories_bucket_owner",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "(kind = 'expense' AND bucket_id IS NOT NULL) OR "
            "(kind IN ('income', 'funding') AND bucket_id IS NULL)",
            name="ck_categories_kind_bucket",
        ),
        UniqueConstraint("id", "user_id", name="uq_categories_id_user_id"),
        UniqueConstraint("user_id", "name", name="uq_categories_user_name"),
        Index("ix_categories_user_kind", "user_id", "kind"),
        Index("ix_categories_user_bucket", "user_id", "bucket_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    bucket_id: Mapped[UUID | None] = mapped_column(Uuid)
    name: Mapped[str] = mapped_column(String(100))
    kind: Mapped[CategoryKind] = mapped_column(
        Enum(
            CategoryKind,
            name="category_kind",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda values: [item.value for item in values],
        )
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
