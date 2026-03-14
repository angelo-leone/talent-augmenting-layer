"""Talent-Augmenting Layer -- Google OAuth authentication.

Uses authlib for the OAuth flow and python-jose for JWT session tokens
stored in secure cookies.
"""
from __future__ import annotations

import datetime
import logging
from typing import Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import Request, Response, HTTPException
from jose import jwt, JWTError
from sqlalchemy import select

from hosted.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    SECRET_KEY,
    APP_URL,
)
from hosted.database import async_session_factory, User

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72
COOKIE_NAME = "tal_session"

oauth = OAuth()


# ---------------------------------------------------------------------------
# OAuth setup
# ---------------------------------------------------------------------------

def setup_oauth(app) -> None:
    """Register the Google OAuth provider on the Starlette/FastAPI app."""
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_session_token(user_id: int, email: str, name: str) -> str:
    """Create a signed JWT containing the user's identity."""
    payload = {
        "sub": str(user_id),
        "email": email,
        "name": name,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> Optional[dict]:
    """Decode and verify a session JWT. Returns the claims dict or None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Request helpers
# ---------------------------------------------------------------------------

def get_current_user(request: Request) -> Optional[dict]:
    """Extract the current user from the session cookie.

    Returns a dict with ``id``, ``email``, ``name`` or None if not authenticated.
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    claims = decode_session_token(token)
    if not claims:
        return None
    return {
        "id": int(claims["sub"]),
        "email": claims.get("email", ""),
        "name": claims.get("name", ""),
    }


def require_auth(request: Request) -> dict:
    """Like ``get_current_user`` but raises 401 if not authenticated."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def set_session_cookie(response: Response, token: str) -> None:
    """Set the session JWT as an httponly cookie."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=APP_URL.startswith("https"),
        samesite="lax",
        max_age=JWT_EXPIRY_HOURS * 3600,
    )


def clear_session_cookie(response: Response) -> None:
    """Remove the session cookie."""
    response.delete_cookie(key=COOKIE_NAME)


# ---------------------------------------------------------------------------
# User upsert
# ---------------------------------------------------------------------------

async def get_or_create_user(google_id: str, email: str, name: str, picture: str = "") -> User:
    """Find existing user by google_id or create a new one. Returns the User row."""
    async with async_session_factory() as session:
        stmt = select(User).where(User.google_id == google_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture,
            )
            session.add(user)
            await session.flush()
            logger.info("Created new user: %s (%s)", name, email)
        else:
            # Update name/picture if changed
            if user.name != name:
                user.name = name
            if picture and user.picture != picture:
                user.picture = picture

        await session.commit()
        # Refresh to get the committed state
        await session.refresh(user)
        return user
