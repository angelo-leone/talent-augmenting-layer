"""MCP OAuth 2.1 Authorization Server Provider.

Implements the OAuthAuthorizationServerProvider protocol from the MCP SDK,
delegating user identity to Google OAuth (the same provider the web app uses).

Flow:
  1. MCP client hits /mcp → gets 401 with resource metadata URL
  2. Client discovers auth endpoints via /.well-known/oauth-authorization-server
  3. Client registers dynamically via /mcp/register
  4. Client opens browser to /mcp/authorize
  5. We redirect to Google login
  6. Google callback → we issue an authorization code
  7. Client exchanges code for access token via /mcp/token
  8. Client sends Bearer token with every MCP request
"""
from __future__ import annotations

import datetime
import json
import logging
import secrets
import time
from typing import Optional

from jose import jwt, JWTError
from pydantic import AnyUrl
from sqlalchemy import select, delete

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from hosted.config import (
    APP_URL,
    SECRET_KEY,
    MCP_ACCESS_TOKEN_EXPIRY,
    MCP_REFRESH_TOKEN_EXPIRY,
    MCP_AUTH_CODE_EXPIRY,
)
from hosted.database import (
    async_session_factory,
    OAuthClient,
    OAuthPendingAuth,
    OAuthAuthorizationCode as OAuthAuthorizationCodeDB,
    OAuthToken as OAuthTokenDB,
)

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"

# ---------------------------------------------------------------------------
# Extended token models (carry user_id for downstream use)
# ---------------------------------------------------------------------------


class TALAuthorizationCode(AuthorizationCode):
    user_id: int


class TALAccessToken(AccessToken):
    user_id: int


class TALRefreshToken(RefreshToken):
    user_id: int


# ---------------------------------------------------------------------------
# Provider implementation
# ---------------------------------------------------------------------------


class TALOAuthProvider(
    OAuthAuthorizationServerProvider[TALAuthorizationCode, TALRefreshToken, TALAccessToken]
):
    """OAuth 2.1 provider backed by PostgreSQL and Google identity."""

    # ── Client registration ──────────────────────────────────────────────

    async def get_client(self, client_id: str) -> Optional[OAuthClientInformationFull]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(OAuthClient).where(OAuthClient.client_id == client_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return _row_to_client_info(row)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        async with async_session_factory() as session:
            row = OAuthClient(
                client_id=client_info.client_id,
                client_secret=client_info.client_secret,
                client_id_issued_at=client_info.client_id_issued_at,
                client_secret_expires_at=client_info.client_secret_expires_at,
                redirect_uris_json=json.dumps(
                    [str(u) for u in (client_info.redirect_uris or [])]
                ),
                token_endpoint_auth_method=client_info.token_endpoint_auth_method,
                grant_types_json=json.dumps(client_info.grant_types or []),
                response_types_json=json.dumps(client_info.response_types or []),
                scope=client_info.scope,
                client_name=client_info.client_name,
                client_uri=str(client_info.client_uri) if client_info.client_uri else None,
            )
            session.add(row)
            await session.commit()

    # ── Authorization ────────────────────────────────────────────────────

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Persist the pending auth state and redirect to Google login.

        Returns a URL that the MCP SDK's AuthorizationHandler will redirect to.
        """
        state_key = secrets.token_urlsafe(32)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(
            seconds=MCP_AUTH_CODE_EXPIRY
        )

        async with async_session_factory() as session:
            row = OAuthPendingAuth(
                state_key=state_key,
                client_id=client.client_id,
                code_challenge=params.code_challenge,
                redirect_uri=str(params.redirect_uri),
                redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
                scopes_json=json.dumps(params.scopes) if params.scopes else None,
                state=params.state,
                resource=params.resource,
                expires_at=expires_at,
            )
            session.add(row)
            await session.commit()

        # Redirect the user's browser to our Google OAuth entry-point.
        # The state_key lets the callback retrieve the pending auth.
        google_auth_url = f"{APP_URL}/mcp/oauth/google/start?mcp_state={state_key}"
        return google_auth_url

    # ── Authorization code ───────────────────────────────────────────────

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> Optional[TALAuthorizationCode]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(OAuthAuthorizationCodeDB).where(
                    OAuthAuthorizationCodeDB.code == authorization_code,
                    OAuthAuthorizationCodeDB.client_id == client.client_id,
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return TALAuthorizationCode(
                code=row.code,
                scopes=json.loads(row.scopes_json) if row.scopes_json else [],
                expires_at=row.expires_at,
                client_id=row.client_id,
                code_challenge=row.code_challenge,
                redirect_uri=AnyUrl(row.redirect_uri),
                redirect_uri_provided_explicitly=row.redirect_uri_provided_explicitly,
                resource=row.resource,
                user_id=row.user_id,
            )

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: TALAuthorizationCode
    ) -> OAuthToken:
        """Exchange an auth code for access + refresh tokens."""
        now = int(time.time())
        jti = secrets.token_urlsafe(32)
        scopes = authorization_code.scopes or []

        # Create JWT access token
        access_token = jwt.encode(
            {
                "sub": str(authorization_code.user_id),
                "client_id": client.client_id,
                "scopes": scopes,
                "jti": jti,
                "iat": now,
                "exp": now + MCP_ACCESS_TOKEN_EXPIRY,
                "iss": APP_URL,
                "aud": authorization_code.resource or f"{APP_URL}/mcp",
            },
            SECRET_KEY,
            algorithm=JWT_ALGORITHM,
        )
        refresh_token_str = secrets.token_urlsafe(48)

        # Persist token metadata
        async with async_session_factory() as session:
            token_row = OAuthTokenDB(
                access_token_jti=jti,
                refresh_token=refresh_token_str,
                client_id=client.client_id,
                user_id=authorization_code.user_id,
                scopes_json=json.dumps(scopes),
                resource=authorization_code.resource,
                access_token_expires_at=now + MCP_ACCESS_TOKEN_EXPIRY,
                refresh_token_expires_at=now + MCP_REFRESH_TOKEN_EXPIRY,
            )
            session.add(token_row)

            # Delete the used authorization code (one-time use)
            await session.execute(
                delete(OAuthAuthorizationCodeDB).where(
                    OAuthAuthorizationCodeDB.code == authorization_code.code
                )
            )
            await session.commit()

        return OAuthToken(
            access_token=access_token,
            token_type="Bearer",
            expires_in=MCP_ACCESS_TOKEN_EXPIRY,
            scope=" ".join(scopes) if scopes else None,
            refresh_token=refresh_token_str,
        )

    # ── Refresh token ────────────────────────────────────────────────────

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> Optional[TALRefreshToken]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(OAuthTokenDB).where(
                    OAuthTokenDB.refresh_token == refresh_token,
                    OAuthTokenDB.client_id == client.client_id,
                    OAuthTokenDB.revoked == False,  # noqa: E712
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return TALRefreshToken(
                token=row.refresh_token,
                client_id=row.client_id,
                scopes=json.loads(row.scopes_json) if row.scopes_json else [],
                expires_at=row.refresh_token_expires_at,
                user_id=row.user_id,
            )

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: TALRefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        """Rotate both access and refresh tokens."""
        now = int(time.time())
        new_jti = secrets.token_urlsafe(32)
        new_refresh = secrets.token_urlsafe(48)
        effective_scopes = scopes if scopes else refresh_token.scopes

        access_token = jwt.encode(
            {
                "sub": str(refresh_token.user_id),
                "client_id": client.client_id,
                "scopes": effective_scopes,
                "jti": new_jti,
                "iat": now,
                "exp": now + MCP_ACCESS_TOKEN_EXPIRY,
                "iss": APP_URL,
                "aud": f"{APP_URL}/mcp",
            },
            SECRET_KEY,
            algorithm=JWT_ALGORITHM,
        )

        async with async_session_factory() as session:
            # Revoke old token row
            result = await session.execute(
                select(OAuthTokenDB).where(
                    OAuthTokenDB.refresh_token == refresh_token.token
                )
            )
            old_row = result.scalar_one_or_none()
            if old_row:
                old_row.revoked = True

            # Insert new token row
            token_row = OAuthTokenDB(
                access_token_jti=new_jti,
                refresh_token=new_refresh,
                client_id=client.client_id,
                user_id=refresh_token.user_id,
                scopes_json=json.dumps(effective_scopes),
                access_token_expires_at=now + MCP_ACCESS_TOKEN_EXPIRY,
                refresh_token_expires_at=now + MCP_REFRESH_TOKEN_EXPIRY,
            )
            session.add(token_row)
            await session.commit()

        return OAuthToken(
            access_token=access_token,
            token_type="Bearer",
            expires_in=MCP_ACCESS_TOKEN_EXPIRY,
            scope=" ".join(effective_scopes) if effective_scopes else None,
            refresh_token=new_refresh,
        )

    # ── Access token verification ────────────────────────────────────────

    async def load_access_token(self, token: str) -> Optional[TALAccessToken]:
        """Stateless JWT verification — no DB hit per request."""
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                audience=f"{APP_URL}/mcp",
            )
        except JWTError:
            return None

        jti = payload.get("jti", "")

        # Check revocation (only for explicit revoke; normal expiry is handled by JWT)
        async with async_session_factory() as session:
            result = await session.execute(
                select(OAuthTokenDB.revoked).where(
                    OAuthTokenDB.access_token_jti == jti
                )
            )
            row = result.scalar_one_or_none()
            if row is True:
                return None

        return TALAccessToken(
            token=token,
            client_id=payload.get("client_id", ""),
            scopes=payload.get("scopes", []),
            expires_at=payload.get("exp"),
            resource=payload.get("aud"),
            user_id=int(payload["sub"]),
        )

    # ── Revocation ───────────────────────────────────────────────────────

    async def revoke_token(
        self, token: TALAccessToken | TALRefreshToken
    ) -> None:
        async with async_session_factory() as session:
            if isinstance(token, TALRefreshToken):
                result = await session.execute(
                    select(OAuthTokenDB).where(
                        OAuthTokenDB.refresh_token == token.token
                    )
                )
            else:
                # Access token — decode JTI
                try:
                    payload = jwt.decode(
                        token.token, SECRET_KEY, algorithms=[JWT_ALGORITHM],
                        options={"verify_aud": False, "verify_exp": False},
                    )
                    jti = payload.get("jti", "")
                except JWTError:
                    return
                result = await session.execute(
                    select(OAuthTokenDB).where(
                        OAuthTokenDB.access_token_jti == jti
                    )
                )

            row = result.scalar_one_or_none()
            if row:
                row.revoked = True
                await session.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _row_to_client_info(row: OAuthClient) -> OAuthClientInformationFull:
    """Convert a DB row to an OAuthClientInformationFull pydantic model."""
    redirect_uris = json.loads(row.redirect_uris_json) if row.redirect_uris_json else []
    return OAuthClientInformationFull(
        client_id=row.client_id,
        client_secret=row.client_secret,
        client_id_issued_at=row.client_id_issued_at,
        client_secret_expires_at=row.client_secret_expires_at,
        redirect_uris=[AnyUrl(u) for u in redirect_uris] if redirect_uris else None,
        token_endpoint_auth_method=row.token_endpoint_auth_method,
        grant_types=json.loads(row.grant_types_json) if row.grant_types_json else None,
        response_types=json.loads(row.response_types_json) if row.response_types_json else None,
        scope=row.scope,
        client_name=row.client_name,
        client_uri=AnyUrl(row.client_uri) if row.client_uri else None,
    )


async def create_authorization_code_for_user(
    user_id: int,
    state_key: str,
) -> str:
    """Called by the Google OAuth callback to mint an authorization code.

    Looks up the pending auth by state_key, creates the code, and returns the
    redirect URL back to the MCP client.
    """
    async with async_session_factory() as session:
        # Load and delete the pending auth
        result = await session.execute(
            select(OAuthPendingAuth).where(OAuthPendingAuth.state_key == state_key)
        )
        pending = result.scalar_one_or_none()
        if pending is None:
            raise ValueError("Pending authorization not found or expired")

        if pending.expires_at < datetime.datetime.utcnow():
            await session.delete(pending)
            await session.commit()
            raise ValueError("Pending authorization expired")

        # Generate authorization code (>= 160 bits entropy)
        code = secrets.token_urlsafe(32)
        code_row = OAuthAuthorizationCodeDB(
            code=code,
            client_id=pending.client_id,
            user_id=user_id,
            code_challenge=pending.code_challenge,
            redirect_uri=pending.redirect_uri,
            redirect_uri_provided_explicitly=pending.redirect_uri_provided_explicitly,
            scopes_json=pending.scopes_json,
            resource=pending.resource,
            expires_at=time.time() + MCP_AUTH_CODE_EXPIRY,
        )
        session.add(code_row)

        # Capture values before deleting
        redirect_uri = pending.redirect_uri
        client_state = pending.state

        await session.delete(pending)
        await session.commit()

    # Build redirect URL back to the MCP client
    return construct_redirect_uri(redirect_uri, code=code, state=client_state)
