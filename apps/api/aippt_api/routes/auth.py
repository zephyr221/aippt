import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlmodel import Session

from ..auth import (
    clear_session_cookie,
    get_current_user,
    get_user_by_email,
    hash_password,
    set_session_cookie,
    upsert_jaccount_user,
    verify_password,
)
from ..config import Settings, get_settings
from ..db import get_session
from ..models import User
from ..schemas import UserCreate, UserLogin, UserRead


router = APIRouter()


def _oauth_serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret, salt="aippt-oauth-state")


def _safe_next(next_url: str) -> str:
    if next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return "/"


def _set_oauth_state_cookie(
    response: Response,
    settings: Settings,
    *,
    state: str,
    next_url: str,
) -> None:
    token = _oauth_serializer(settings).dumps({"state": state, "next": _safe_next(next_url)})
    response.set_cookie(
        settings.oauth_state_cookie_name,
        token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=10 * 60,
    )


def _load_oauth_state(settings: Settings, token: str | None) -> dict[str, str]:
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing OAuth state")
    try:
        payload = _oauth_serializer(settings).loads(token, max_age=10 * 60)
    except BadSignature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("state"), str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")
    return payload


def _profile_entity(profile_envelope: dict) -> dict:
    entities = profile_envelope.get("entities") or []
    if not entities or not isinstance(entities[0], dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="jAccount profile has no user entity",
        )
    return entities[0]


def _profile_affiliation(profile: dict) -> str:
    organize = profile.get("organize")
    if isinstance(organize, dict) and organize.get("name"):
        return str(organize["name"])
    identities = profile.get("identities")
    if isinstance(identities, list) and identities and isinstance(identities[0], dict):
        return str(identities[0].get("organizeName") or "")
    return ""


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    response: Response,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User:
    email = payload.email.lower()
    if get_user_by_email(session, email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=email,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    set_session_cookie(response, user, settings)
    return user


@router.post("/login", response_model=UserRead)
def login(
    payload: UserLogin,
    response: Response,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User:
    user = get_user_by_email(session, payload.email.lower())
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    set_session_cookie(response, user, settings)
    return user


@router.get("/jaccount/login")
def jaccount_login(
    next: str = "/",
    dev_login: str | None = None,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    if dev_login and settings.dev_allow_fake_login:
        user = upsert_jaccount_user(
            session,
            jaccount=dev_login,
            code=f"DEV{dev_login}",
            name=f"开发用户 {dev_login}",
            email=f"{dev_login}@sjtu.edu.cn",
            user_type="student",
            affiliation="DEV",
        )
        session.commit()
        response = RedirectResponse(url=_safe_next(next), status_code=status.HTTP_302_FOUND)
        set_session_cookie(response, user, settings)
        return response

    if not settings.jaccount_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="jAccount is not configured",
        )

    state = secrets.token_urlsafe(24)
    params = {
        "response_type": "code",
        "client_id": settings.jaccount_client_id,
        "redirect_uri": settings.jaccount_redirect_uri,
        "scope": settings.jaccount_scope,
        "state": state,
    }
    response = RedirectResponse(
        url=f"{settings.jaccount_authorize_url}?{urlencode(params)}",
        status_code=status.HTTP_302_FOUND,
    )
    _set_oauth_state_cookie(response, settings, state=state, next_url=next)
    return response


@router.get("/jaccount/callback")
def jaccount_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    oauth_state = request.cookies.get(settings.oauth_state_cookie_name)
    payload = _load_oauth_state(settings, oauth_state)
    if not state or state != payload["state"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth state mismatch")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code")

    with httpx.Client(timeout=15) as client:
        token_response = client.post(
            settings.jaccount_token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.jaccount_redirect_uri,
                "client_id": settings.jaccount_client_id,
                "client_secret": settings.jaccount_client_secret,
            },
            headers={"Accept": "application/json"},
        )
        if token_response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="jAccount token exchange failed",
            )
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="jAccount token response missing access token",
            )

        profile_response = client.get(
            settings.jaccount_userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="jAccount profile fetch failed",
            )
        profile = _profile_entity(profile_response.json())

    user = upsert_jaccount_user(
        session,
        jaccount=str(profile.get("account") or ""),
        code=str(profile.get("code") or ""),
        name=str(profile.get("name") or ""),
        email=str(profile.get("email") or ""),
        user_type=str(profile.get("userType") or ""),
        affiliation=_profile_affiliation(profile),
    )
    session.commit()

    response = RedirectResponse(
        url=_safe_next(str(payload.get("next") or "/")),
        status_code=status.HTTP_302_FOUND,
    )
    response.delete_cookie(settings.oauth_state_cookie_name)
    set_session_cookie(response, user, settings)
    return response


@router.post("/logout")
def logout(response: Response, settings: Settings = Depends(get_settings)) -> dict[str, str]:
    clear_session_cookie(response, settings)
    return {"status": "ok"}


@router.get("/logout")
def logout_redirect(settings: Settings = Depends(get_settings)) -> RedirectResponse:
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    clear_session_cookie(response, settings)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
