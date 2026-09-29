"""Create people and IOU events.

Revision ID: 20260928_0006
Revises: 20260924_0005
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260928_0006"
down_revision: str | None = "20260924_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "people",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "user_id", name="uq_people_id_user"),
        sa.UniqueConstraint("user_id", "name", name="uq_people_user_name"),
    )
    op.create_index("ix_people_user_name", "people", ["user_id", "name"])
    op.create_table(
        "iou_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=24), nullable=False),
        sa.Column("adjustment_direction", sa.String(length=16), nullable=True),
        sa.Column("amount_cad", sa.Numeric(14, 2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "event_type IN ('borrowed', 'lent', 'repayment_received', "
            "'repayment_made', 'adjustment')",
            name="iou_event_type",
        ),
        sa.CheckConstraint(
            "adjustment_direction IN ('owes_user', 'user_owes')",
            name="iou_adjustment_direction",
        ),
        sa.CheckConstraint("amount_cad > 0", name="ck_iou_events_positive_amount"),
        sa.CheckConstraint(
            "(event_type = 'adjustment' AND adjustment_direction IS NOT NULL) OR "
            "(event_type <> 'adjustment' AND adjustment_direction IS NULL)",
            name="ck_iou_events_adjustment_direction",
        ),
        sa.ForeignKeyConstraint(
            ["person_id", "user_id"],
            ["people.id", "people.user_id"],
            name="fk_iou_events_person_owner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_iou_events_user_person_date",
        "iou_events",
        ["user_id", "person_id", "date"],
    )


def downgrade() -> None:
    op.drop_table("iou_events")
    op.drop_table("people")
