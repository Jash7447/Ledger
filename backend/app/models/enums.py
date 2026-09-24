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
