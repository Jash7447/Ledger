from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.models.bucket import Bucket
from app.models.category import Category
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.dashboard import (
    DashboardResponse,
    DashboardSummary,
    SpendingBreakdownItem,
)
from app.schemas.financial import TransactionResponse
from app.services.accounts import list_accounts_with_balances
from app.services.budgets import list_budgets_with_progress
from app.services.goals import dashboard_goals
from app.services.people import get_iou_totals
from app.services.runway import get_runway_estimate


def month_bounds(selected_month: str | None) -> tuple[date, date]:
    today = date.today()
    if selected_month is None:
        start = today.replace(day=1)
    else:
        year, month = (int(part) for part in selected_month.split("-"))
        start = date(year, month, 1)
    if start.month == 12:
        next_month = date(start.year + 1, 1, 1)
    else:
        next_month = date(start.year, start.month + 1, 1)
    return start, next_month


def get_dashboard(db: Session, user_id: UUID, selected_month: str | None) -> DashboardResponse:
    period_start, next_month = month_bounds(selected_month)
    period_filters = (
        Transaction.user_id == user_id,
        Transaction.date >= period_start,
        Transaction.date < next_month,
    )
    income, expenses = db.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.type == TransactionType.INCOME, Transaction.amount_cad),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.type == TransactionType.EXPENSE, Transaction.amount_cad),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ),
        ).where(*period_filters)
    ).one()
    income_amount = Decimal(income)
    expense_amount = Decimal(expenses)
    current_balance = sum(
        (balance for _, balance in list_accounts_with_balances(db, user_id)),
        Decimal("0.00"),
    )
    iou_totals = get_iou_totals(db, user_id)

    bucket_rows = db.execute(
        select(
            Bucket.id,
            func.coalesce(Bucket.name, "Uncategorized"),
            func.sum(Transaction.amount_cad),
        )
        .select_from(Transaction)
        .outerjoin(
            Bucket,
            and_(Bucket.id == Transaction.bucket_id, Bucket.user_id == Transaction.user_id),
        )
        .where(*period_filters, Transaction.type == TransactionType.EXPENSE)
        .group_by(Bucket.id, Bucket.name)
        .order_by(func.sum(Transaction.amount_cad).desc())
    ).all()
    category_rows = db.execute(
        select(
            Category.id,
            func.coalesce(Category.name, "Uncategorized"),
            func.sum(Transaction.amount_cad),
        )
        .select_from(Transaction)
        .outerjoin(
            Category,
            and_(
                Category.id == Transaction.category_id,
                Category.user_id == Transaction.user_id,
            ),
        )
        .where(*period_filters, Transaction.type == TransactionType.EXPENSE)
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount_cad).desc())
    ).all()
    education_spending = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount_cad), Decimal("0.00")))
        .select_from(Transaction)
        .join(
            Bucket,
            and_(Bucket.id == Transaction.bucket_id, Bucket.user_id == Transaction.user_id),
        )
        .where(
            *period_filters,
            Transaction.type == TransactionType.EXPENSE,
            Bucket.name == "Education",
        )
    )
    recent = list(
        db.scalars(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
            .limit(5)
        ).all()
    )
    major = list(
        db.scalars(
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.is_major_purchase.is_(True),
            )
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
            .limit(5)
        ).all()
    )
    return DashboardResponse(
        period_start=period_start,
        period_end=next_month - timedelta(days=1),
        summary=DashboardSummary(
            current_balance_cad=current_balance,
            monthly_income_cad=income_amount,
            monthly_expenses_cad=expense_amount,
            monthly_savings_cad=income_amount - expense_amount,
            education_spending_cad=Decimal(education_spending or 0),
            money_owed_to_user_cad=iou_totals.owed_to_user_cad,
            money_owed_to_others_cad=iou_totals.user_owes_cad,
        ),
        spending_by_bucket=[
            SpendingBreakdownItem(id=item_id, name=name, amount_cad=Decimal(amount))
            for item_id, name, amount in bucket_rows
        ],
        spending_by_category=[
            SpendingBreakdownItem(id=item_id, name=name, amount_cad=Decimal(amount))
            for item_id, name, amount in category_rows
        ],
        budget_progress=list_budgets_with_progress(
            db, user_id, period_start.strftime("%Y-%m")
        ),
        recent_transactions=[TransactionResponse.model_validate(item) for item in recent],
        major_purchases=[TransactionResponse.model_validate(item) for item in major],
        goals=dashboard_goals(db, user_id),
        runway=get_runway_estimate(db, user_id),
    )
