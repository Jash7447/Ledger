from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.settings import (
    CurrencySettingsResponse,
    CurrencySettingsUpdate,
    RunwaySettingsResponse,
    RunwaySettingsUpdate,
)
from app.services.settings import (
    get_currency_settings,
    get_runway_settings,
    update_currency_settings,
    update_runway_settings,
)

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


@router.get("/runway", response_model=RunwaySettingsResponse)
def get_runway(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> RunwaySettingsResponse:
    return get_runway_settings(db, current_user.id)


@router.patch("/runway", response_model=RunwaySettingsResponse)
def update_runway(
    data: RunwaySettingsUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> RunwaySettingsResponse:
    return update_runway_settings(db, current_user.id, data)
