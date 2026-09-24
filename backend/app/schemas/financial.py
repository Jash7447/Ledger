from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    AccountType,
    CategoryKind,
    ExpenseClassification,
    SortDirection,
    TransactionSortField,
    TransactionType,
)


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: AccountType
    currency: str = Field(default="CAD", pattern=r"^[A-Z]{3}$")


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: AccountType | None = None


class AccountResponse(AccountCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AccountWithBalance(AccountResponse):
    balance_cad: Decimal


class BucketCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class BucketResponse(BucketCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: CategoryKind
    bucket_id: UUID | None = None

    @model_validator(mode="after")
    def validate_bucket_usage(self) -> "CategoryCreate":
        if self.kind == CategoryKind.EXPENSE and self.bucket_id is None:
            raise ValueError("Expense categories require a bucket")
        if self.kind != CategoryKind.EXPENSE and self.bucket_id is not None:
            raise ValueError("Income and funding categories cannot have a spending bucket")
        return self


class CategoryResponse(CategoryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class BucketWithCategories(BucketResponse):
    categories: list[CategoryResponse]


class ClassificationCatalogResponse(BaseModel):
    buckets: list[BucketWithCategories]
    income_categories: list[CategoryResponse]
    funding_categories: list[CategoryResponse]


class TransactionCreate(BaseModel):
    account_id: UUID
    destination_account_id: UUID | None = None
    type: TransactionType
    amount_cad: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    date: date_type
    description: str = Field(min_length=1, max_length=255)
    bucket_id: UUID | None = None
    category_id: UUID | None = None
    notes: str | None = None
    expense_classification: ExpenseClassification | None = None
    is_major_purchase: bool = False

    @model_validator(mode="after")
    def validate_transaction_shape(self) -> "TransactionCreate":
        if self.type == TransactionType.TRANSFER:
            if self.destination_account_id is None:
                raise ValueError("Transfers require a destination account")
            if self.destination_account_id == self.account_id:
                raise ValueError("Transfer accounts must be different")
            if self.bucket_id is not None or self.category_id is not None:
                raise ValueError("Transfers cannot have a bucket or category")
            if self.expense_classification is not None or self.is_major_purchase:
                raise ValueError("Transfers cannot have expense attributes")
        elif self.destination_account_id is not None:
            raise ValueError("Only transfers can have a destination account")

        if self.type == TransactionType.INCOME:
            if self.bucket_id is not None:
                raise ValueError("Income cannot have a spending bucket")
            if self.expense_classification is not None or self.is_major_purchase:
                raise ValueError("Income cannot have expense attributes")
        return self


class TransactionUpdate(BaseModel):
    account_id: UUID | None = None
    destination_account_id: UUID | None = None
    type: TransactionType | None = None
    amount_cad: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    date: date_type | None = None
    description: str | None = Field(default=None, min_length=1, max_length=255)
    bucket_id: UUID | None = None
    category_id: UUID | None = None
    notes: str | None = None
    expense_classification: ExpenseClassification | None = None
    is_major_purchase: bool | None = None


class TransactionResponse(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class TransactionListQuery(BaseModel):
    search: str | None = Field(default=None, max_length=100)
    date_from: date_type | None = None
    date_to: date_type | None = None
    account_id: UUID | None = None
    bucket_id: UUID | None = None
    category_id: UUID | None = None
    type: TransactionType | None = None
    is_major_purchase: bool | None = None
    sort_by: TransactionSortField = TransactionSortField.DATE
    sort_direction: SortDirection = SortDirection.DESC
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)

    @model_validator(mode="after")
    def validate_date_range(self) -> "TransactionListQuery":
        if self.date_from is not None and self.date_to is not None:
            if self.date_from > self.date_to:
                raise ValueError("date_from must be on or before date_to")
        return self
