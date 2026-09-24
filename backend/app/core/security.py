from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings

ALGORITHM = "HS256"
TOKEN_ISSUER = "ledger-api"
password_hash = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hash.hash("ledger-dummy-password")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    return password_hash.verify(password, encoded_hash)


def create_session_token(user_id: UUID) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "session",
        "iss": TOKEN_ISSUER,
        "iat": now,
        "exp": now + timedelta(minutes=settings.auth_session_expire_minutes),
    }
    return jwt.encode(payload, settings.auth_secret_key, algorithm=ALGORITHM)


def decode_session_token(token: str) -> UUID | None:
    try:
        payload = jwt.decode(
            token,
            get_settings().auth_secret_key,
            algorithms=[ALGORITHM],
            issuer=TOKEN_ISSUER,
        )
        if payload.get("type") != "session":
            return None
        return UUID(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        return None
