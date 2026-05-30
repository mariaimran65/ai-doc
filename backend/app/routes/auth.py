import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_utils import create_jwt, get_current_user
from app.config import settings
from app.database import get_db
from app.models.session import Session
from app.models.user import User

router = APIRouter()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/login")
async def login():
    """Redirect the browser to Google's OAuth 2.0 consent screen.

    Builds the authorization URL with the required scopes and a random state
    value, then issues a 302 redirect. The browser follows it to Google.

    Returns:
        302 redirect to Google's authorization endpoint.
    """
    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": settings.google_oauth_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": secrets.token_urlsafe(16),
        "access_type": "online",
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/callback")
async def callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Handle the OAuth callback from Google.

    Exchanges the authorization code for an access token, fetches the user
    profile, upserts the user row, creates a session record, issues a signed
    JWT, sets it in an httpOnly cookie, and redirects the browser to the
    frontend.

    Args:
        code: Authorization code provided by Google.
        state: Opaque state value echoed back by Google (not yet verified — see review note).
        db: Injected async database session.

    Returns:
        302 redirect to the frontend with the JWT set as an httpOnly cookie.

    Raises:
        HTTPException 400 if the token exchange or profile fetch fails.
    """
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": settings.google_oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if not token_resp.is_success:
            raise HTTPException(status_code=400, detail="Token exchange failed")
        access_token = token_resp.json()["access_token"]

        profile_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if not profile_resp.is_success:
            raise HTTPException(status_code=400, detail="Failed to fetch user profile")
        profile = profile_resp.json()

    result = await db.execute(
        select(User).where(
            User.provider == "google", User.provider_user_id == profile["id"]
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=profile["email"],
            provider="google",
            provider_user_id=profile["id"],
            avatar_url=profile.get("picture"),
        )
        db.add(user)
    else:
        user.avatar_url = profile.get("picture")
        user.updated_at = datetime.now(timezone.utc)

    await db.flush()

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    session_token = secrets.token_urlsafe(32)
    db.add(Session(user_id=user.id, token=session_token, expires_at=expires_at))
    await db.commit()

    jwt_token = create_jwt(
        sub=str(user.id),
        email=user.email,
        session_token=session_token,
        exp=expires_at,
    )

    response = RedirectResponse(url=settings.frontend_url, status_code=302)
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=False,
        samesite="lax",
        expires=int(expires_at.timestamp()),
    )
    return response


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's identity from their JWT.

    Args:
        current_user: JWT payload injected by the get_current_user dependency.

    Returns:
        Dict with user_id and email.
    """
    return {"user_id": current_user["sub"], "email": current_user["email"]}


@router.post("/logout")
async def logout(response: Response):
    """Invalidate the session by clearing the JWT cookie.

    Args:
        response: FastAPI response object used to delete the cookie.

    Returns:
        Confirmation message.
    """
    response.delete_cookie("access_token")
    return {"detail": "Logged out"}
