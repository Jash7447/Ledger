from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.bucket import Bucket
from app.models.category import Category
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.education import EducationCategoryTotal, EducationReport
from app.schemas.financial import TransactionResponse


def get_education_report(
    db: Session, user_id: UUID, date_from: date, date_to: date
) -> EducationReport:
    filters = (
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE,
        Transaction.date >= date_from,
        Transaction.date <= date_to,
        Bucket.name == "Education",
    )
    base_join = (
        select(Transaction)
        .join(
            Bucket,
            and_(Bucket.id == Transaction.bucket_id, Bucket.user_id == Transaction.user_id),
        )
        .where(*filters)
    )
    transactions = list(
        db.scalars(
            base_join.order_by(Transaction.date.desc(), Transaction.created_at.desc()).limit(100)
        ).all()
    )
    total, count = db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount_cad), Decimal("0.00")),
            func.count(Transaction.id),
        )
        .select_from(Transaction)
        .join(
            Bucket,
            and_(Bucket.id == Transaction.bucket_id, Bucket.user_id == Transaction.user_id),
        )
        .where(*filters)
    ).one()
    category_rows = db.execute(
        select(Category.id, Category.name, func.sum(Transaction.amount_cad))
        .select_from(Transaction)
        .join(
            Bucket,
            and_(Bucket.id == Transaction.bucket_id, Bucket.user_id == Transaction.user_id),
        )
        .join(
            Category,
            and_(
                Category.id == Transaction.category_id,
                Category.user_id == Transaction.user_id,
            ),
        )
        .where(*filters)
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount_cad).desc())
    ).all()
    return EducationReport(
        date_from=date_from,
        date_to=date_to,
        total_spent_cad=Decimal(total),
        transaction_count=int(count),
        spending_by_category=[
            EducationCategoryTotal(
                category_id=category_id,
                category_name=name,
                amount_cad=Decimal(amount),
            )
            for category_id, name, amount in category_rows
        ],
        transactions=[TransactionResponse.model_validate(item) for item in transactions],
    )
