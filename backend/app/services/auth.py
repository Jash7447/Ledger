from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from app.core.security import DUMMY_PASSWORD_HASH, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import SignUpRequest
from app.services.catalog import initialize_user_catalog


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(db: Session, data: SignUpRequest) -> User:
    email = normalize_email(str(data.email))
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise EmailAlreadyRegisteredError

    user = User(
        email=email,
        display_name=data.display_name.strip(),
        password_hash=hash_password(data.password),
    )
    db.add(user)
    try:
        db.flush()
        initialize_user_catalog(db, user.id)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise EmailAlreadyRegisteredError from error
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    if user is None:
        verify_password(password, DUMMY_PASSWORD_HASH)
        raise InvalidCredentialsError
    if not user.is_active or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError
    return user
