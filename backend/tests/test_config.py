import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_cors_origins_accept_comma_separated_values() -> None:
    settings = Settings(backend_cors_origins="http://localhost:3000, http://localhost:3001")
    assert settings.backend_cors_origins == ["http://localhost:3000", "http://localhost:3001"]


def test_production_rejects_development_auth_settings() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production")
