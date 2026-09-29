from uuid import UUID

from sqlalchemy.orm import Session

from app.models.currency_setting import CurrencySetting
from app.schemas.settings import CurrencySettingsResponse, CurrencySettingsUpdate


def get_currency_settings(db: Session, user_id: UUID) -> CurrencySettingsResponse:
    setting = db.get(CurrencySetting, user_id)
    if setting is None:
        setting = CurrencySetting(user_id=user_id)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return CurrencySettingsResponse.model_validate(setting)


def update_currency_settings(
    db: Session, user_id: UUID, data: CurrencySettingsUpdate
) -> CurrencySettingsResponse:
    get_currency_settings(db, user_id)
    setting = db.get(CurrencySetting, user_id)
    assert setting is not None
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(setting, field, value)
    db.commit()
    db.refresh(setting)
    return CurrencySettingsResponse.model_validate(setting)
