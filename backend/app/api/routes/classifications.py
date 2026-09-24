from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.financial import (
    BucketResponse,
    BucketWithCategories,
    CategoryResponse,
    ClassificationCatalogResponse,
)
from app.services.classifications import list_classifications

router = APIRouter()


@router.get("", response_model=ClassificationCatalogResponse)
def get_catalog(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ClassificationCatalogResponse:
    buckets, expense, income, funding = list_classifications(db, current_user.id)
    expense_by_bucket = {
        bucket.id: [
            CategoryResponse.model_validate(category)
            for category in expense
            if category.bucket_id == bucket.id
        ]
        for bucket in buckets
    }
    return ClassificationCatalogResponse(
        buckets=[
            BucketWithCategories(
                **BucketResponse.model_validate(bucket).model_dump(),
                categories=expense_by_bucket[bucket.id],
            )
            for bucket in buckets
        ],
        income_categories=[CategoryResponse.model_validate(item) for item in income],
        funding_categories=[CategoryResponse.model_validate(item) for item in funding],
    )
