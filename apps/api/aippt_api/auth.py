from datetime import datetime, timezone
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Response, status
from itsdangerous import BadSignature, URLSafeTimedSerializer
from passlib.context import CryptContext
from sqlmodel import Session, select

from .config import Settings, get_settings
from .db import get_session
from .models import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret, salt="aippt-session")


def set_session_cookie(response: Response, user: User, settings: Settings) -> None:
    token = _serializer(settings).dumps({"user_id": str(user.id), "issued_at": datetime.now(timezone.utc).isoformat()})
    response.set_cookie(
        settings.session_cookie_name,
        token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=60 * 60 * 24 * 14,
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(settings.session_cookie_name)


def get_current_user(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
    aippt_session: str | None = Cookie(default=None),
) -> User:
    if not aippt_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = _serializer(settings).loads(aippt_session, max_age=60 * 60 * 24 * 14)
        user_id = UUID(payload["user_id"])
    except (BadSignature, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from None

    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email.lower())).first()

