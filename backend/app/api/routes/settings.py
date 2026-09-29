from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.settings import CurrencySettingsResponse, CurrencySettingsUpdate
from app.services.settings import get_currency_settings, update_currency_settings

router = APIRouter()


@router.get("/currency", response_model=CurrencySettingsResponse)
def get_currency(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CurrencySettingsResponse:
    return get_currency_settings(db, current_user.id)


@router.patch("/currency", response_model=CurrencySettingsResponse)
def update_currency(
    data: CurrencySettingsUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CurrencySettingsResponse:
    return update_currency_settings(db, current_user.id, data)
