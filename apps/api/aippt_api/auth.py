from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Response, status
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
    if not password_hash:
        return False
    return pwd_context.verify(password, password_hash)


def _serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret, salt="aippt-session")


def set_session_cookie(response: Response, user: User, settings: Settings) -> None:
    token = _serializer(settings).dumps(
        {"user_id": str(user.id), "issued_at": datetime.now(timezone.utc).isoformat()}
    )
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
    request: Request,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User:
    aippt_session = request.cookies.get(settings.session_cookie_name)
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


def get_user_by_jaccount(session: Session, jaccount: str) -> User | None:
    return session.exec(select(User).where(User.jaccount == jaccount)).first()


def upsert_jaccount_user(
    session: Session,
    *,
    jaccount: str,
    code: str = "",
    name: str = "",
    email: str = "",
    user_type: str = "",
    affiliation: str = "",
) -> User:
    if not jaccount:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="jAccount is empty")

    normalized_email = _jaccount_email(jaccount, email)
    user = get_user_by_jaccount(session, jaccount) or get_user_by_email(session, normalized_email)
    display_name = name or jaccount
    now = datetime.now(timezone.utc)

    if user is None:
        user = User(
            jaccount=jaccount,
            code=code,
            email=normalized_email,
            display_name=display_name,
            password_hash="",
            affiliation=affiliation,
            user_type=user_type,
            last_login_at=now,
        )
        session.add(user)
        session.flush()
        return user

    user.jaccount = jaccount
    user.code = code or user.code
    user.email = normalized_email or user.email
    user.display_name = display_name
    user.affiliation = affiliation or user.affiliation
    user.user_type = user_type or user.user_type
    user.last_login_at = now
    session.add(user)
    session.flush()
    return user


def _jaccount_email(jaccount: str, email: str) -> str:
    email = (email or "").strip().lower()
    if email and "@" in email:
        return email
    safe_jaccount = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in jaccount.lower())
    return f"{safe_jaccount}@sjtu.edu.cn"
