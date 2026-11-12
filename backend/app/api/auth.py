from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.security import (
    SESSION_COOKIE,
    check_password,
    create_session_token,
    login_throttle,
    require_auth,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    password: str = Field(min_length=1, max_length=200)


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response, settings: Settings = Depends(get_settings)) -> dict:
    client = request.client.host if request.client else "unknown"
    if login_throttle.is_locked(client):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many failed attempts. Try again later.")
    if not check_password(body.password, settings):
        login_throttle.record_failure(client)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid password")
    login_throttle.reset(client)
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(settings),
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/",
    )
    return {"ok": True}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/me")
def me(_: dict = Depends(require_auth)) -> dict:
    return {"authenticated": True}
