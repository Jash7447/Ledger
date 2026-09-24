"""Enforce category kind and bucket compatibility.

Revision ID: 20260921_0003
Revises: 20260921_0002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260921_0003"
down_revision: str | None = "20260921_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_categories_kind_bucket",
        "categories",
        "(kind = 'expense' AND bucket_id IS NOT NULL) OR "
        "(kind IN ('income', 'funding') AND bucket_id IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_categories_kind_bucket", "categories", type_="check")
