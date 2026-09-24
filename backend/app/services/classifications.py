from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.bucket import Bucket
from app.models.category import Category
from app.models.enums import CategoryKind


def list_classifications(
    db: Session, user_id: UUID
) -> tuple[list[Bucket], list[Category], list[Category], list[Category]]:
    buckets = list(
        db.scalars(
            select(Bucket).where(Bucket.user_id == user_id).order_by(Bucket.name)
        ).all()
    )
    categories = list(
        db.scalars(
            select(Category).where(Category.user_id == user_id).order_by(Category.name)
        ).all()
    )
    expense = [category for category in categories if category.kind == CategoryKind.EXPENSE]
    income = [category for category in categories if category.kind == CategoryKind.INCOME]
    funding = [category for category in categories if category.kind == CategoryKind.FUNDING]
    return buckets, expense, income, funding
