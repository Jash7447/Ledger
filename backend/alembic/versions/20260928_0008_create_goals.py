"""Create savings goals.

Revision ID: 20260928_0008
Revises: 20260928_0007
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260928_0008"
down_revision: str | None = "20260928_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("target_amount_cad", sa.Numeric(14, 2), nullable=False),
        sa.Column("current_amount_cad", sa.Numeric(14, 2), server_default="0.00", nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=12), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("target_amount_cad > 0", name="ck_goals_positive_target"),
        sa.CheckConstraint("current_amount_cad >= 0", name="ck_goals_nonnegative_progress"),
        sa.CheckConstraint(
            "status IN ('active', 'paused', 'completed', 'cancelled')",
            name="goal_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_goals_user_name"),
    )
    op.create_index("ix_goals_user_status", "goals", ["user_id", "status"])


def downgrade() -> None:
    op.drop_table("goals")
