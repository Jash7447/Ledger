from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    app_name: str = "Ledger API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://ledger:ledger_dev_password@localhost:5433/ledger"
    backend_cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    auth_secret_key: str = "local-development-secret-change-before-deployment"
    auth_session_expire_minutes: int = 480
    auth_cookie_name: str = "ledger_session"
    auth_cookie_secure: bool = False

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        unsafe_secrets = {
            "local-development-secret-change-before-deployment",
            "replace-with-a-random-secret-before-deployment",
        }
        if self.environment.lower() == "production":
            if self.auth_secret_key in unsafe_secrets or len(self.auth_secret_key) < 32:
                raise ValueError("AUTH_SECRET_KEY must be replaced in production")
            if not self.auth_cookie_secure:
                raise ValueError("AUTH_COOKIE_SECURE must be true in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
