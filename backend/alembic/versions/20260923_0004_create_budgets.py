"""Create monthly budgets.

Revision ID: 20260923_0004
Revises: 20260921_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260923_0004"
down_revision: str | None = "20260921_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "budgets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("bucket_id", sa.Uuid(), nullable=True),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("amount_cad", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("amount_cad > 0", name="ck_budgets_positive_amount"),
        sa.CheckConstraint("period_end >= period_start", name="ck_budgets_valid_period"),
        sa.CheckConstraint(
            "(bucket_id IS NOT NULL AND category_id IS NULL) OR "
            "(bucket_id IS NULL AND category_id IS NOT NULL)",
            name="ck_budgets_single_scope",
        ),
        sa.ForeignKeyConstraint(
            ["bucket_id", "user_id"],
            ["buckets.id", "buckets.user_id"],
            name="fk_budgets_bucket_owner",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["category_id", "user_id"],
            ["categories.id", "categories.user_id"],
            name="fk_budgets_category_owner",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "bucket_id", "period_start", name="uq_budgets_user_bucket_period"
        ),
        sa.UniqueConstraint(
            "user_id",
            "category_id",
            "period_start",
            name="uq_budgets_user_category_period",
        ),
    )
    op.create_index("ix_budgets_user_period", "budgets", ["user_id", "period_start"])


def downgrade() -> None:
    op.drop_table("budgets")
