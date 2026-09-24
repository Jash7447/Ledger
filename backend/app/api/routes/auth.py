from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.config import get_settings
from app.core.security import create_session_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import SessionResponse, SignInRequest, SignUpRequest, UserResponse
from app.services.auth import authenticate_user, register_user

router = APIRouter()


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.auth_session_expire_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/signup", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def signup(
    data: SignUpRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> SessionResponse:
    user = register_user(db, data)
    set_session_cookie(response, create_session_token(user.id))
    return SessionResponse(user=UserResponse.model_validate(user))


@router.post("/login", response_model=SessionResponse)
def login(
    data: SignInRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> SessionResponse:
    user = authenticate_user(db, str(data.email), data.password)
    set_session_cookie(response, create_session_token(user.id))
    return SessionResponse(user=UserResponse.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.auth_cookie_name,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> User:
    return current_user
