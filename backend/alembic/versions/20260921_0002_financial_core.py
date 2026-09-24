"""Create core financial tables and default classifications.

Revision ID: 20260921_0002
Revises: 20260921_0001
"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision: str = "20260921_0002"
down_revision: str | None = "20260921_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EXPENSE_CATALOG: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Essentials",
        (
            "Rent",
            "Groceries",
            "Utilities",
            "Phone",
            "Internet",
            "Transportation",
            "Insurance",
            "Healthcare",
            "Household",
        ),
    ),
    (
        "Education",
        (
            "Tuition",
            "Student Fees",
            "Health Fees",
            "Books",
            "Course Materials",
            "Software",
            "Exams",
            "Certifications",
            "Other Education",
        ),
    ),
    ("Lifestyle", ("Clothing", "Shoes", "Electronics", "Personal Care", "Shopping", "Gifts")),
    (
        "Leisure",
        ("Restaurants", "Coffee", "Takeout", "Entertainment", "Movies", "Events", "Gaming"),
    ),
    (
        "Travel",
        ("Flights", "Hotels", "Local Transport", "Travel Food", "Visa/Immigration", "Other Travel"),
    ),
    ("Financial", ("Savings", "Investments", "Debt Repayment")),
    ("Other", ("Miscellaneous",)),
)
INCOME_CATEGORIES = ("Salary", "Freelance", "Scholarship", "Interest", "Refund", "Other Income")
FUNDING_CATEGORIES = ("Family Support", "Gift", "Loan", "Other Funding")


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="CAD", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "type IN ('chequing', 'savings', 'credit_card', 'cash', 'other')",
            name="account_type",
        ),
        sa.CheckConstraint("currency = upper(currency)", name="ck_accounts_currency_uppercase"),
        sa.CheckConstraint("length(currency) = 3", name="ck_accounts_currency_length"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "user_id", name="uq_accounts_id_user_id"),
        sa.UniqueConstraint("user_id", "name", name="uq_accounts_user_name"),
    )
    op.create_index("ix_accounts_user_active", "accounts", ["user_id", "is_active"])

    op.create_table(
        "buckets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "user_id", name="uq_buckets_id_user_id"),
        sa.UniqueConstraint("user_id", "name", name="uq_buckets_user_name"),
    )
    op.create_index("ix_buckets_user_id", "buckets", ["user_id"])

    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("bucket_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "kind IN ('expense', 'income', 'funding')", name="category_kind"
        ),
        sa.ForeignKeyConstraint(
            ["bucket_id", "user_id"],
            ["buckets.id", "buckets.user_id"],
            name="fk_categories_bucket_owner",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "user_id", name="uq_categories_id_user_id"),
        sa.UniqueConstraint("user_id", "name", name="uq_categories_user_name"),
    )
    op.create_index("ix_categories_user_kind", "categories", ["user_id", "kind"])
    op.create_index(
        "ix_categories_user_bucket", "categories", ["user_id", "bucket_id"]
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("destination_account_id", sa.Uuid(), nullable=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("amount_cad", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("bucket_id", sa.Uuid(), nullable=True),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("expense_classification", sa.String(length=20), nullable=True),
        sa.Column("is_major_purchase", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "type IN ('expense', 'income', 'transfer')", name="transaction_type"
        ),
        sa.CheckConstraint(
            "expense_classification IN ('fixed', 'variable')",
            name="expense_classification",
        ),
        sa.CheckConstraint("amount_cad > 0", name="ck_transactions_positive_amount"),
        sa.CheckConstraint(
            "(type = 'transfer' AND destination_account_id IS NOT NULL) OR "
            "(type <> 'transfer' AND destination_account_id IS NULL)",
            name="ck_transactions_transfer_destination",
        ),
        sa.CheckConstraint(
            "destination_account_id IS NULL OR destination_account_id <> account_id",
            name="ck_transactions_distinct_transfer_accounts",
        ),
        sa.CheckConstraint(
            "type <> 'transfer' OR (bucket_id IS NULL AND category_id IS NULL)",
            name="ck_transactions_transfer_uncategorized",
        ),
        sa.CheckConstraint(
            "type = 'expense' OR expense_classification IS NULL",
            name="ck_transactions_expense_classification",
        ),
        sa.CheckConstraint(
            "type = 'expense' OR is_major_purchase = false",
            name="ck_transactions_major_purchase_expense",
        ),
        sa.ForeignKeyConstraint(
            ["account_id", "user_id"],
            ["accounts.id", "accounts.user_id"],
            name="fk_transactions_account_owner",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["bucket_id", "user_id"],
            ["buckets.id", "buckets.user_id"],
            name="fk_transactions_bucket_owner",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["category_id", "user_id"],
            ["categories.id", "categories.user_id"],
            name="fk_transactions_category_owner",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["destination_account_id", "user_id"],
            ["accounts.id", "accounts.user_id"],
            name="fk_transactions_destination_account_owner",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transactions_user_date", "transactions", ["user_id", "date"])
    op.create_index(
        "ix_transactions_user_account_date",
        "transactions",
        ["user_id", "account_id", "date"],
    )
    op.create_index(
        "ix_transactions_user_type_date", "transactions", ["user_id", "type", "date"]
    )
    op.create_index(
        "ix_transactions_user_category_date",
        "transactions",
        ["user_id", "category_id", "date"],
    )
    op.create_index(
        "ix_transactions_user_major_date",
        "transactions",
        ["user_id", "is_major_purchase", "date"],
    )

    _backfill_default_catalogs()


def _backfill_default_catalogs() -> None:
    connection = op.get_bind()
    user_ids = connection.execute(sa.text("SELECT id FROM users")).scalars().all()
    for user_id in user_ids:
        for bucket_name, category_names in EXPENSE_CATALOG:
            bucket_id = uuid4()
            connection.execute(
                sa.text(
                    "INSERT INTO buckets (id, user_id, name) "
                    "VALUES (:id, :user_id, :name)"
                ),
                {"id": bucket_id, "user_id": user_id, "name": bucket_name},
            )
            for category_name in category_names:
                connection.execute(
                    sa.text(
                        "INSERT INTO categories (id, user_id, bucket_id, name, kind) "
                        "VALUES (:id, :user_id, :bucket_id, :name, 'expense')"
                    ),
                    {
                        "id": uuid4(),
                        "user_id": user_id,
                        "bucket_id": bucket_id,
                        "name": category_name,
                    },
                )
        for kind, category_names in (
            ("income", INCOME_CATEGORIES),
            ("funding", FUNDING_CATEGORIES),
        ):
            for category_name in category_names:
                connection.execute(
                    sa.text(
                        "INSERT INTO categories (id, user_id, bucket_id, name, kind) "
                        "VALUES (:id, :user_id, NULL, :name, :kind)"
                    ),
                    {
                        "id": uuid4(),
                        "user_id": user_id,
                        "name": category_name,
                        "kind": kind,
                    },
                )


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("categories")
    op.drop_table("buckets")
    op.drop_table("accounts")
