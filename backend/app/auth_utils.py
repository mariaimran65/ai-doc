from datetime import datetime
from typing import Optional

import jwt
from fastapi import Cookie, HTTPException, status

from app.config import settings


def create_jwt(sub: str, email: str, session_token: str, exp: datetime) -> str:
    """Encode a signed JWT containing the user identity and session reference.

    Args:
        sub: User UUID as a string.
        email: User email address.
        session_token: Opaque token stored in the sessions table.
        exp: Token expiry as a timezone-aware datetime.

    Returns:
        Signed JWT string.
    """
    payload = {"sub": sub, "email": email, "session_token": session_token, "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_jwt(token: str) -> dict:
    """Decode and verify a JWT, raising HTTP 401 on any failure.

    Args:
        token: Signed JWT string.

    Returns:
        Decoded payload dict with keys: sub, email, session_token, exp.

    Raises:
        HTTPException 401 if the token is expired or invalid.
    """
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(access_token: Optional[str] = Cookie(default=None)) -> dict:
    """FastAPI dependency that extracts and validates the JWT from the request cookie.

    Args:
        access_token: JWT read from the httpOnly 'access_token' cookie.

    Returns:
        Decoded JWT payload.

    Raises:
        HTTPException 401 if no cookie is present or the token is invalid.
    """
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return decode_jwt(access_token)
