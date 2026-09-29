from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.bucket import Bucket
from app.models.category import Category
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.analytics import (
    AnalyticsBreakdownItem,
    AnalyticsResponse,
    AnalyticsSummary,
    MonthlyAnalyticsItem,
)
from app.schemas.financial import TransactionResponse

ZERO = Decimal("0.00")


def get_analytics(db: Session, user_id: UUID, date_from: date, date_to: date) -> AnalyticsResponse:
    transactions = list(
        db.scalars(
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
            )
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        ).all()
    )
    bucket_names = {
        item_id: name
        for item_id, name in db.execute(
            select(Bucket.id, Bucket.name).where(Bucket.user_id == user_id)
        )
    }
    category_names = {
        item_id: name
        for item_id, name in db.execute(
            select(Category.id, Category.name).where(Category.user_id == user_id)
        )
    }
    bucket_totals: dict[UUID | None, Decimal] = defaultdict(lambda: ZERO)
    category_totals: dict[UUID | None, Decimal] = defaultdict(lambda: ZERO)
    classification_totals: dict[str, Decimal] = defaultdict(lambda: ZERO)
    monthly = {
        month: {"income": ZERO, "expenses": ZERO} for month in _months_between(date_from, date_to)
    }
    income = ZERO
    expenses = ZERO
    education = ZERO
    major_total = ZERO
    major_purchases: list[Transaction] = []

    for transaction in transactions:
        month = transaction.date.strftime("%Y-%m")
        if transaction.type == TransactionType.INCOME:
            income += transaction.amount_cad
            monthly[month]["income"] += transaction.amount_cad
        elif transaction.type == TransactionType.EXPENSE:
            expenses += transaction.amount_cad
            monthly[month]["expenses"] += transaction.amount_cad
            bucket_totals[transaction.bucket_id] += transaction.amount_cad
            category_totals[transaction.category_id] += transaction.amount_cad
            classification = transaction.expense_classification
            label = classification.value.title() if classification is not None else "Unclassified"
            classification_totals[label] += transaction.amount_cad
            if bucket_names.get(transaction.bucket_id) == "Education":
                education += transaction.amount_cad
            if transaction.is_major_purchase:
                major_total += transaction.amount_cad
                major_purchases.append(transaction)

    return AnalyticsResponse(
        date_from=date_from,
        date_to=date_to,
        summary=AnalyticsSummary(
            income_cad=income,
            expenses_cad=expenses,
            savings_cad=income - expenses,
            education_spending_cad=education,
            major_purchase_spending_cad=major_total,
        ),
        spending_by_bucket=_breakdown(bucket_totals, bucket_names),
        spending_by_category=_breakdown(category_totals, category_names),
        fixed_vs_variable=[
            AnalyticsBreakdownItem(name=name, amount_cad=amount)
            for name, amount in sorted(
                classification_totals.items(), key=lambda item: item[1], reverse=True
            )
        ],
        monthly_trend=[
            MonthlyAnalyticsItem(
                month=month,
                income_cad=values["income"],
                expenses_cad=values["expenses"],
                savings_cad=values["income"] - values["expenses"],
            )
            for month, values in monthly.items()
        ],
        major_purchases=[TransactionResponse.model_validate(item) for item in major_purchases],
    )


def _breakdown(
    totals: dict[UUID | None, Decimal], names: dict[UUID, str]
) -> list[AnalyticsBreakdownItem]:
    return [
        AnalyticsBreakdownItem(
            id=item_id,
            name=names.get(item_id, "Uncategorized") if item_id else "Uncategorized",
            amount_cad=amount,
        )
        for item_id, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]


def _months_between(date_from: date, date_to: date) -> list[str]:
    months: list[str] = []
    year, month = date_from.year, date_from.month
    while (year, month) <= (date_to.year, date_to.month):
        months.append(f"{year:04d}-{month:02d}")
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
    return months
