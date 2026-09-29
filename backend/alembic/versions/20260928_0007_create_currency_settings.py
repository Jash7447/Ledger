"""Create per-user currency settings.

Revision ID: 20260928_0007
Revises: 20260928_0006
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260928_0007"
down_revision: str | None = "20260928_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "currency_settings",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("display_currency", sa.String(length=3), server_default="CAD", nullable=False),
        sa.Column(
            "cad_to_inr_rate", sa.Numeric(precision=14, scale=4), server_default="70.0000", nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "display_currency IN ('CAD', 'INR')", name="display_currency"
        ),
        sa.CheckConstraint(
            "cad_to_inr_rate > 0", name="ck_currency_settings_positive_rate"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("currency_settings")
