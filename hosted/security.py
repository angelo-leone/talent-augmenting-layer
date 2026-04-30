"""Security middleware and rate limiting for the TAOS hosted app.

This module provides three things:

1. ``SecurityHeadersMiddleware``: adds standard hardening response headers
   (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy,
   Permissions-Policy). HSTS is sent only over TLS to avoid breaking
   local development.

2. ``limiter``: a ``slowapi.Limiter`` instance used as a FastAPI dependency
   on routes that need per-IP or per-user throttling.

3. ``register_security``: wires (1) and (2) into a FastAPI app in one call.

Notes on the CSP:
  Templates contain ``<style>`` blocks and ``<script>`` blocks inline, plus
  a ``<script src="https://cdn.jsdelivr.net/...">`` for Chart.js. Until we
  refactor to nonce/hashed CSP, ``script-src`` permits ``cdn.jsdelivr.net``
  and ``style-src`` permits ``'unsafe-inline'``. The frame-ancestors
  directive is ``'none'`` to block clickjacking. ``form-action 'self'``
  prevents form-redirect phishing.

Notes on the rate limiter:
  Storage is in-process. For a single-instance Render deployment this is
  fine; if you scale to >1 instance, switch ``storage_uri`` to a Redis URL.
"""
from __future__ import annotations

import os
from typing import Awaitable, Callable

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

_CSP_DIRECTIVES = (
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https://lh3.googleusercontent.com https://*.googleusercontent.com",
    "font-src 'self' data:",
    "connect-src 'self'",
    "frame-ancestors 'none'",
    "form-action 'self'",
    "base-uri 'self'",
    "object-src 'none'",
)

CONTENT_SECURITY_POLICY = "; ".join(_CSP_DIRECTIVES)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Append hardening headers to every response."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)

        response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=(), payment=(), usb=(), interest-cohort=()",
        )

        # HSTS only when the request was over HTTPS. Behind Render's proxy this
        # arrives as X-Forwarded-Proto=https; uvicorn is started with
        # --proxy-headers so request.url.scheme is correct.
        if request.url.scheme == "https":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        return response


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def _key_func(request: Request) -> str:
    """Rate-limit key.

    For authenticated requests, use the user id; otherwise use the remote IP.
    The user id is set by the auth middleware on ``request.state.user_id``
    when present.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        return f"user:{user_id}"
    return f"ip:{get_remote_address(request)}"


_DEFAULT_LIMITS = [os.getenv("TAOS_RATE_LIMIT_DEFAULT", "120/minute")]

limiter = Limiter(
    key_func=_key_func,
    default_limits=_DEFAULT_LIMITS,
    headers_enabled=True,
    storage_uri=os.getenv("TAOS_RATE_LIMIT_STORAGE", "memory://"),
)


# Per-route convenience aliases used as FastAPI dependencies.
LIMIT_LOGIN = "10/minute"
LIMIT_ASSESS = "30/minute"
LIMIT_API = "60/minute"
LIMIT_MCP = "240/minute"


def register_security(app: FastAPI) -> None:
    """Attach security middleware and rate limiter to a FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    # SecurityHeadersMiddleware must be outermost so it covers responses
    # produced by other middlewares (including SlowAPI's 429 response).
    app.add_middleware(SecurityHeadersMiddleware)
