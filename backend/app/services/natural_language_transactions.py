import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.bucket import Bucket
from app.models.category import Category
from app.models.enums import CategoryKind, TransactionType
from app.schemas.financial import TransactionCreate
from app.schemas.natural_language import NaturalLanguageTransactionProposal
from app.services.financial_validation import validate_transaction_references

AMOUNT_PATTERN = re.compile(
    r"(?:(?:CAD)\s*\$?\s*|\$\s*)(\d[\d,]*(?:\.\d{1,2})?)|"
    r"(\d[\d,]*(?:\.\d{1,2})?)\s*(?:CAD)\b",
    re.IGNORECASE,
)
ISO_DATE_PATTERN = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")

INCOME_WORDS = ("received", "earned", "income", "salary", "paid me", "refund")
EXPENSE_WORDS = ("spent", "paid", "bought", "purchase", "cost", "expense")

CATEGORY_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Restaurants", ("dinner", "lunch", "breakfast", "restaurant", "meal")),
    ("Coffee", ("coffee", "cafe")),
    ("Takeout", ("takeout", "delivery")),
    ("Groceries", ("grocery", "groceries", "supermarket")),
    ("Rent", ("rent",)),
    ("Transportation", ("bus", "transit", "uber", "taxi", "gas")),
    ("Phone", ("phone bill", "mobile")),
    ("Internet", ("internet", "wifi")),
    ("Tuition", ("tuition",)),
    ("Books", ("textbook", "book")),
    ("Software", ("software", "app subscription")),
    ("Clothing", ("clothes", "shirt", "pants")),
    ("Shoes", ("shoes", "sneakers")),
    ("Electronics", ("laptop", "phone", "electronics")),
    ("Entertainment", ("entertainment", "concert")),
    ("Movies", ("movie", "cinema")),
    ("Flights", ("flight", "airfare")),
    ("Hotels", ("hotel",)),
)

INCOME_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Salary", ("salary", "paycheque", "paycheck", "wages")),
    ("Freelance", ("freelance", "client payment")),
    ("Scholarship", ("scholarship", "bursary")),
    ("Interest", ("interest",)),
    ("Refund", ("refund",)),
    ("Family Support", ("family support", "parents sent")),
    ("Gift", ("gift",)),
)


def propose_transaction(
    db: Session, user_id: UUID, source_text: str
) -> NaturalLanguageTransactionProposal:
    text = " ".join(source_text.strip().split())
    lowered = text.lower()
    warnings: list[str] = []
    errors: list[str] = []
    transaction_type = _transaction_type(lowered)
    if transaction_type is None:
        errors.append("Could not determine whether this is an expense or income")
    amount = _amount(text)
    if amount is None or amount <= 0:
        errors.append("Could not find a positive CAD amount")
        amount = None
    transaction_date, date_warning = _transaction_date(lowered)
    if date_warning:
        warnings.append(date_warning)

    accounts = list(
        db.scalars(
            select(Account)
            .where(Account.user_id == user_id, Account.is_active.is_(True))
            .order_by(Account.created_at, Account.name)
        ).all()
    )
    account = next(
        (item for item in accounts if item.name.lower() in lowered),
        accounts[0] if accounts else None,
    )
    if account is None:
        errors.append("Create an active account before confirming this transaction")
    elif len(accounts) > 1 and account.name.lower() not in lowered:
        warnings.append(f"Using {account.name}; review the suggested account")

    bucket: Bucket | None = None
    category: Category | None = None
    if transaction_type is not None:
        category = _suggest_category(db, user_id, transaction_type, lowered)
        if category is not None and category.bucket_id is not None:
            bucket = db.scalar(
                select(Bucket).where(
                    Bucket.id == category.bucket_id, Bucket.user_id == user_id
                )
            )
        if category is None:
            warnings.append("No category suggestion was available")

    threshold = Decimal("150.00")
    is_major = transaction_type == TransactionType.EXPENSE and bool(
        amount is not None and amount >= threshold
    )
    ready = not errors
    if ready:
        assert transaction_type is not None and amount is not None and account is not None
        candidate = TransactionCreate(
            account_id=account.id,
            type=transaction_type,
            amount_cad=amount,
            date=transaction_date,
            description=text[:255],
            bucket_id=bucket.id if bucket else None,
            category_id=category.id if category else None,
            is_major_purchase=is_major,
        )
        validate_transaction_references(db, user_id, candidate)
    return NaturalLanguageTransactionProposal(
        source_text=text,
        type=transaction_type,
        amount_cad=amount,
        date=transaction_date,
        description=text[:255],
        account_id=account.id if account else None,
        account_name=account.name if account else None,
        bucket_id=bucket.id if bucket else None,
        bucket_name=bucket.name if bucket else None,
        category_id=category.id if category else None,
        category_name=category.name if category else None,
        is_major_purchase=is_major,
        ready_to_confirm=ready,
        warnings=warnings,
        errors=errors,
    )


def _transaction_type(text: str) -> TransactionType | None:
    income = any(word in text for word in INCOME_WORDS)
    expense = any(word in text for word in EXPENSE_WORDS) and "paid me" not in text
    if income and not expense:
        return TransactionType.INCOME
    if expense and not income:
        return TransactionType.EXPENSE
    return None


def _amount(text: str) -> Decimal | None:
    match = AMOUNT_PATTERN.search(text)
    if match is None:
        return None
    raw = (match.group(1) or match.group(2)).replace(",", "")
    try:
        return Decimal(raw).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def _transaction_date(text: str) -> tuple[date, str | None]:
    today = date.today()
    if "yesterday" in text:
        return today - timedelta(days=1), None
    if "today" in text:
        return today, None
    match = ISO_DATE_PATTERN.search(text)
    if match:
        try:
            return date.fromisoformat(match.group(1)), None
        except ValueError:
            pass
    return today, "No recognized date found; defaulted to today"


def _suggest_category(
    db: Session, user_id: UUID, transaction_type: TransactionType, text: str
) -> Category | None:
    categories = list(
        db.scalars(select(Category).where(Category.user_id == user_id)).all()
    )
    aliases = CATEGORY_ALIASES if transaction_type == TransactionType.EXPENSE else INCOME_ALIASES
    fallback = "Miscellaneous" if transaction_type == TransactionType.EXPENSE else "Other Income"
    suggested_name = next(
        (name for name, words in aliases if any(word in text for word in words)),
        fallback,
    )
    expected_kinds = (
        {CategoryKind.EXPENSE}
        if transaction_type == TransactionType.EXPENSE
        else {CategoryKind.INCOME, CategoryKind.FUNDING}
    )
    return next(
        (
            item
            for item in categories
            if item.name == suggested_name and item.kind in expected_kinds
        ),
        None,
    )
