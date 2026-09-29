from enum import StrEnum


class AccountType(StrEnum):
    CHEQUING = "chequing"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    OTHER = "other"


class CategoryKind(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"
    FUNDING = "funding"


class TransactionType(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"


class ExpenseClassification(StrEnum):
    FIXED = "fixed"
    VARIABLE = "variable"


class TransactionSortField(StrEnum):
    DATE = "date"
    AMOUNT = "amount"
    DESCRIPTION = "description"
    CREATED_AT = "created_at"


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class RecurringFrequency(StrEnum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class IOUEventType(StrEnum):
    BORROWED = "borrowed"
    LENT = "lent"
    REPAYMENT_RECEIVED = "repayment_received"
    REPAYMENT_MADE = "repayment_made"
    ADJUSTMENT = "adjustment"


class IOUAdjustmentDirection(StrEnum):
    OWES_USER = "owes_user"
    USER_OWES = "user_owes"


class DisplayCurrency(StrEnum):
    CAD = "CAD"
    INR = "INR"


class GoalStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
