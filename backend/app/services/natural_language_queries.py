import re
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.models.bucket import Bucket
from app.models.category import Category
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.natural_language import NaturalLanguageQueryResponse
from app.services.people import list_people

ZERO = Decimal("0.00")
FOOD_CATEGORIES = ("Groceries", "Restaurants", "Coffee", "Takeout", "Travel Food")


def answer_financial_query(
    db: Session, user_id: UUID, question: str
) -> NaturalLanguageQueryResponse:
    text = " ".join(question.strip().split())
    lowered = text.lower().rstrip("?.!")
    date_from, date_to, period_label = _date_range(lowered)

    if "biggest purchase" in lowered or "largest purchase" in lowered:
        return _biggest_purchases(db, user_id, date_from, date_to, period_label)
    if "owe" in lowered:
        return _iou_answer(db, user_id, lowered)
    if "tuition" in lowered:
        return _category_spending(
            db, user_id, ("Tuition",), "tuition", date_from, date_to, period_label
        )
    if "education" in lowered:
        return _bucket_spending(db, user_id, "Education", date_from, date_to, period_label)
    if "food" in lowered:
        return _category_spending(
            db, user_id, FOOD_CATEGORIES, "food", date_from, date_to, period_label
        )
    if "income" in lowered or "earn" in lowered:
        return _transaction_total(
            db,
            user_id,
            TransactionType.INCOME,
            "income",
            date_from,
            date_to,
            period_label,
        )
    if "spend" in lowered or "spent" in lowered or "expense" in lowered:
        return _transaction_total(
            db,
            user_id,
            TransactionType.EXPENSE,
            "spending",
            date_from,
            date_to,
            period_label,
        )
    return NaturalLanguageQueryResponse(
        intent="unsupported",
        answer=(
            "I can answer questions about spending, income, food, tuition, education, "
            "major purchases, and money owed to or from a person."
        ),
        structured_data={"supported": False},
    )


def _transaction_total(
    db: Session,
    user_id: UUID,
    transaction_type: TransactionType,
    label: str,
    date_from: date | None,
    date_to: date | None,
    period_label: str,
) -> NaturalLanguageQueryResponse:
    filters = [
        Transaction.user_id == user_id,
        Transaction.type == transaction_type,
    ]
    _append_dates(filters, date_from, date_to)
    amount, count = db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount_cad), ZERO),
            func.count(Transaction.id),
        ).where(*filters)
    ).one()
    total = Decimal(amount)
    return NaturalLanguageQueryResponse(
        intent=f"{label}_total",
        answer=f"Your {label} {period_label} was {total:.2f} CAD across {count} transaction(s).",
        amount_cad=total,
        count=count,
        structured_data={
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "transaction_type": transaction_type.value,
        },
    )


def _category_spending(
    db: Session,
    user_id: UUID,
    category_names: tuple[str, ...],
    label: str,
    date_from: date | None,
    date_to: date | None,
    period_label: str,
) -> NaturalLanguageQueryResponse:
    filters = [
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE,
        Category.user_id == user_id,
        Category.name.in_(category_names),
    ]
    _append_dates(filters, date_from, date_to)
    amount, count = db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount_cad), ZERO),
            func.count(Transaction.id),
        )
        .select_from(Transaction)
        .join(
            Category,
            and_(
                Category.id == Transaction.category_id,
                Category.user_id == Transaction.user_id,
            ),
        )
        .where(*filters)
    ).one()
    total = Decimal(amount)
    return NaturalLanguageQueryResponse(
        intent=f"{label}_spending",
        answer=(
            f"Your {label} spending {period_label} was {total:.2f} CAD "
            f"across {count} transaction(s)."
        ),
        amount_cad=total,
        count=count,
        structured_data={"categories": list(category_names)},
    )


def _bucket_spending(
    db: Session,
    user_id: UUID,
    bucket_name: str,
    date_from: date | None,
    date_to: date | None,
    period_label: str,
) -> NaturalLanguageQueryResponse:
    filters = [
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE,
        Bucket.user_id == user_id,
        Bucket.name == bucket_name,
    ]
    _append_dates(filters, date_from, date_to)
    amount, count = db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount_cad), ZERO),
            func.count(Transaction.id),
        )
        .select_from(Transaction)
        .join(
            Bucket,
            and_(Bucket.id == Transaction.bucket_id, Bucket.user_id == Transaction.user_id),
        )
        .where(*filters)
    ).one()
    total = Decimal(amount)
    return NaturalLanguageQueryResponse(
        intent=f"{bucket_name.lower()}_spending",
        answer=(
            f"Your {bucket_name.lower()} spending {period_label} was "
            f"{total:.2f} CAD across {count} transaction(s)."
        ),
        amount_cad=total,
        count=count,
        structured_data={"bucket": bucket_name},
    )


def _biggest_purchases(
    db: Session,
    user_id: UUID,
    date_from: date | None,
    date_to: date | None,
    period_label: str,
) -> NaturalLanguageQueryResponse:
    filters = [
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE,
        Transaction.is_major_purchase.is_(True),
    ]
    _append_dates(filters, date_from, date_to)
    purchases = list(
        db.scalars(
            select(Transaction)
            .where(*filters)
            .order_by(Transaction.amount_cad.desc(), Transaction.date.desc())
            .limit(5)
        ).all()
    )
    total = sum((item.amount_cad for item in purchases), ZERO)
    answer = (
        f"Your largest marked purchase {period_label} was "
        f"{purchases[0].description} at {purchases[0].amount_cad:.2f} CAD."
        if purchases
        else f"You have no marked major purchases {period_label}."
    )
    return NaturalLanguageQueryResponse(
        intent="biggest_purchases",
        answer=answer,
        amount_cad=total,
        count=len(purchases),
        structured_data={
            "purchases": [
                {
                    "id": str(item.id),
                    "description": item.description,
                    "amount_cad": str(item.amount_cad),
                    "date": item.date.isoformat(),
                }
                for item in purchases
            ]
        },
    )


def _iou_answer(db: Session, user_id: UUID, question: str) -> NaturalLanguageQueryResponse:
    people = list_people(db, user_id)
    person = next((item for item in people if item.name.lower() in question), None)
    if person is None:
        return NaturalLanguageQueryResponse(
            intent="person_iou",
            answer="I could not find that person in your People records.",
            amount_cad=ZERO,
            count=0,
            structured_data={"person_found": False},
        )
    asks_owed_to_user = bool(re.search(r"(?:does|do)\s+.+\s+owe\s+me|owed\s+to\s+me", question))
    expected_direction = "owed_to_user" if asks_owed_to_user else "user_owes"
    amount = person.outstanding_amount_cad if person.direction == expected_direction else ZERO
    if asks_owed_to_user:
        answer = f"{person.name} owes you {amount:.2f} CAD."
    else:
        answer = f"You owe {person.name} {amount:.2f} CAD."
    return NaturalLanguageQueryResponse(
        intent="person_iou",
        answer=answer,
        amount_cad=amount,
        count=person.event_count,
        structured_data={
            "person_id": str(person.id),
            "person_name": person.name,
            "direction": expected_direction,
        },
    )


def _date_range(question: str) -> tuple[date | None, date | None, str]:
    today = date.today()
    if "this month" in question:
        return today.replace(day=1), today, "this month"
    if "last month" in question:
        this_month = today.replace(day=1)
        end = this_month - timedelta(days=1)
        return end.replace(day=1), end, "last month"
    if "this year" in question:
        return date(today.year, 1, 1), today, "this year"
    return None, None, "across your recorded history"


def _append_dates(
    filters: list[ColumnElement[bool]], date_from: date | None, date_to: date | None
) -> None:
    if date_from is not None:
        filters.append(Transaction.date >= date_from)
    if date_to is not None:
        filters.append(Transaction.date <= date_to)
