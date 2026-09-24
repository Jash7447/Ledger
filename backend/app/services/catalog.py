from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.bucket import Bucket
from app.models.category import Category
from app.models.enums import CategoryKind

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


def initialize_user_catalog(db: Session, user_id: UUID) -> None:
    existing_buckets = {
        bucket.name: bucket
        for bucket in db.scalars(select(Bucket).where(Bucket.user_id == user_id)).all()
    }
    existing_categories = set(
        db.scalars(select(Category.name).where(Category.user_id == user_id)).all()
    )

    for bucket_name, category_names in EXPENSE_CATALOG:
        bucket = existing_buckets.get(bucket_name)
        if bucket is None:
            bucket = Bucket(user_id=user_id, name=bucket_name)
            db.add(bucket)
            db.flush()
            existing_buckets[bucket_name] = bucket
        for category_name in category_names:
            if category_name not in existing_categories:
                db.add(
                    Category(
                        user_id=user_id,
                        bucket_id=bucket.id,
                        name=category_name,
                        kind=CategoryKind.EXPENSE,
                    )
                )
                existing_categories.add(category_name)

    for kind, names in (
        (CategoryKind.INCOME, INCOME_CATEGORIES),
        (CategoryKind.FUNDING, FUNDING_CATEGORIES),
    ):
        for category_name in names:
            if category_name not in existing_categories:
                db.add(
                    Category(
                        user_id=user_id,
                        bucket_id=None,
                        name=category_name,
                        kind=kind,
                    )
                )
                existing_categories.add(category_name)
