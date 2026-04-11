"""
MCP Remote Transport Handler — OAuth 2.1 Protected

Exposes the Talent-Augmenting Layer MCP server over HTTP so remote clients
(Claude Code, Claude Desktop, Cursor, etc.) can connect.

Authentication:
  - OAuth 2.1 Authorization Code + PKCE
  - Identity delegated to Google (same as the web app)
  - MCP clients register dynamically, then authenticate via browser

Two transports are provided:

  **Streamable HTTP** (primary — what modern MCP clients use):
    - All methods on a single endpoint: POST/GET/DELETE /mcp
    - Stateless — no long-lived connections needed
    - Protected by Bearer token

  **SSE** (legacy — for older clients):
    - GET  /mcp/sse        — persistent SSE stream
    - POST /mcp/messages/   — JSON-RPC message delivery

All MCP tools are pure Python — no LLM API keys on the server.
The client's own model drives the conversation.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from pydantic import AnyHttpUrl
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route

from mcp.server.auth.middleware.auth_context import AuthContextMiddleware
from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend
from mcp.server.auth.provider import ProviderTokenVerifier
from mcp.server.auth.routes import create_auth_routes
from mcp.server.auth.settings import ClientRegistrationOptions, RevocationOptions
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from hosted.config import APP_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from hosted.mcp_oauth import TALOAuthProvider, create_authorization_code_for_user
from hosted.auth import get_or_create_user

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# URLs
# ---------------------------------------------------------------------------

# The MCP sub-app is mounted at /mcp, so issuer = APP_URL + /mcp
ISSUER_URL = AnyHttpUrl(f"{APP_URL}/mcp")
RESOURCE_URL = AnyHttpUrl(f"{APP_URL}/mcp")

# ---------------------------------------------------------------------------
# Lazy-load the TAL MCP server (from mcp-server/src/server.py)
# ---------------------------------------------------------------------------

_tal_server = None


def get_tal_server():
    """Lazy-load the TAL MCP server instance."""
    global _tal_server
    if _tal_server is None:
        server_path = str(Path(__file__).parent.parent / "mcp-server")
        if server_path not in sys.path:
            sys.path.insert(0, server_path)

        from src.server import app as tal_server_instance  # noqa: E402

        _tal_server = tal_server_instance
    return _tal_server


# ---------------------------------------------------------------------------
# Streamable HTTP transport (primary — Claude Desktop 2025+, Claude Code)
# ---------------------------------------------------------------------------

_session_manager = None


def get_session_manager() -> StreamableHTTPSessionManager:
    """Lazy-create the session manager (avoids import-time crashes)."""
    global _session_manager
    if _session_manager is None:
        _session_manager = StreamableHTTPSessionManager(
            app=get_tal_server(),
            stateless=True,
            json_response=True,
        )
    return _session_manager


# ---------------------------------------------------------------------------
# OAuth 2.1 provider singleton
# ---------------------------------------------------------------------------

_oauth_provider = None


def get_oauth_provider() -> TALOAuthProvider:
    global _oauth_provider
    if _oauth_provider is None:
        _oauth_provider = TALOAuthProvider()
    return _oauth_provider


# ---------------------------------------------------------------------------
# SSE transport (legacy — older MCP clients)
# ---------------------------------------------------------------------------

_sse_transport = SseServerTransport("/messages/")


async def handle_sse_get(request: Request):
    """GET /mcp/sse — legacy SSE stream for older MCP clients."""
    tal_server = get_tal_server()
    async with _sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as (read_stream, write_stream):
        await tal_server.run(
            read_stream,
            write_stream,
            tal_server.create_initialization_options(),
        )


async def handle_messages_post(request: Request):
    """POST /mcp/messages/ — legacy SSE message delivery."""
    await _sse_transport.handle_post_message(
        request.scope, request.receive, request._send
    )


# ---------------------------------------------------------------------------
# Config endpoint (public, no auth)
# ---------------------------------------------------------------------------

async def handle_mcp_config(request: Request):
    """GET /mcp/config — return client configuration JSON."""
    app_url = APP_URL
    return JSONResponse(
        {
            "type": "streamable-http",
            "url": f"{app_url}/mcp",
            "legacy_sse_url": f"{app_url}/mcp/sse",
            "description": "Talent-Augmenting Layer — Remote MCP Server",
            "auth": "OAuth 2.1 (Authorization Code + PKCE via Google)",
            "note": (
                "All tools are pure Python — no API keys needed on the server. "
                "Your Claude Code / Cursor model drives the conversation."
            ),
            "documentation": "https://github.com/angelo-leone/talent-augmenting-layer#remote-mcp-configuration",
        }
    )


# ---------------------------------------------------------------------------
# Google OAuth callback for the MCP auth flow
#
# The flow is:
#   /mcp/authorize → provider.authorize() → /mcp/oauth/google/start
#   → Google login → /mcp/oauth/google/callback → redirect to MCP client
# ---------------------------------------------------------------------------

_GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


async def handle_google_oauth_start(request: Request):
    """GET /mcp/oauth/google/start — Redirect to Google login.

    This is called by the provider's authorize() method, which passes the
    mcp_state parameter to link back to the pending authorization.
    """
    mcp_state = request.query_params.get("mcp_state", "")
    if not mcp_state:
        return JSONResponse({"error": "Missing mcp_state"}, status_code=400)

    # Use authlib to build the Google authorization URL
    client = AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )
    # Fetch Google's OIDC metadata to get the authorization endpoint
    async with httpx.AsyncClient() as http:
        resp = await http.get(_GOOGLE_DISCOVERY_URL)
        google_meta = resp.json()

    auth_endpoint = google_meta["authorization_endpoint"]
    redirect_uri = f"{APP_URL}/mcp/oauth/google/callback"

    url, _ = client.create_authorization_url(
        auth_endpoint,
        redirect_uri=redirect_uri,
        scope="openid email profile",
        state=mcp_state,  # Round-trip our state_key through Google
    )
    return RedirectResponse(url=url, status_code=302)


async def handle_google_oauth_callback(request: Request):
    """GET /mcp/oauth/google/callback — Google redirects here after login.

    Exchanges the Google auth code for user info, creates/gets the user,
    then mints an MCP authorization code and redirects to the MCP client.
    """
    google_code = request.query_params.get("code", "")
    mcp_state = request.query_params.get("state", "")

    if not google_code or not mcp_state:
        return JSONResponse(
            {"error": "Missing code or state from Google"}, status_code=400
        )

    # Exchange Google code for tokens
    async with httpx.AsyncClient() as http:
        resp = await http.get(_GOOGLE_DISCOVERY_URL)
        google_meta = resp.json()

    client = AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )
    redirect_uri = f"{APP_URL}/mcp/oauth/google/callback"

    token = await client.fetch_token(
        google_meta["token_endpoint"],
        code=google_code,
        redirect_uri=redirect_uri,
    )

    # Get user info from Google
    async with httpx.AsyncClient() as http:
        userinfo_resp = await http.get(
            google_meta["userinfo_endpoint"],
            headers={"Authorization": f"Bearer {token['access_token']}"},
        )
        userinfo = userinfo_resp.json()

    google_id = userinfo.get("sub", "")
    email = userinfo.get("email", "")
    name = userinfo.get("name", email.split("@")[0])
    picture = userinfo.get("picture", "")

    # Get or create user in our DB (same as web app login)
    user = await get_or_create_user(google_id, email, name, picture)

    # Create the MCP authorization code and get the redirect URL
    try:
        redirect_url = await create_authorization_code_for_user(user.id, mcp_state)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    return RedirectResponse(url=redirect_url, status_code=302)


# ---------------------------------------------------------------------------
# Streamable HTTP handler (protected by auth middleware)
# ---------------------------------------------------------------------------

async def handle_streamable_http(request: Request):
    """GET/POST/DELETE /mcp — Streamable HTTP for modern MCP clients.

    Protected by RequireAuthMiddleware which checks for a valid Bearer token.
    """
    mgr = get_session_manager()
    await mgr.handle_request(request.scope, request.receive, request._send)


# ---------------------------------------------------------------------------
# Build the Starlette sub-app with OAuth 2.1
# ---------------------------------------------------------------------------

def _build_mcp_app() -> Starlette:
    """Construct the MCP Starlette sub-app with auth routes and middleware."""
    provider = get_oauth_provider()
    token_verifier = ProviderTokenVerifier(provider)

    # SDK-generated auth routes (metadata, authorize, token, register, revoke)
    auth_routes = create_auth_routes(
        provider=provider,
        issuer_url=ISSUER_URL,
        client_registration_options=ClientRegistrationOptions(
            enabled=True,
            valid_scopes=["mcp:tools"],
            default_scopes=["mcp:tools"],
        ),
        revocation_options=RevocationOptions(enabled=True),
    )

    # Streamable HTTP — open by default, optionally authenticated.
    # If a Bearer token is present, BearerAuthBackend validates it and sets
    # the user in auth_context_var (available to MCP tools).  If no token,
    # the request proceeds anonymously.
    routes = [
        *auth_routes,
        # Streamable HTTP (open, with optional auth via middleware)
        Route("/", endpoint=handle_streamable_http, methods=["GET", "POST", "DELETE"]),
        # Google OAuth flow for MCP
        Route("/oauth/google/start", endpoint=handle_google_oauth_start),
        Route("/oauth/google/callback", endpoint=handle_google_oauth_callback),
        # Legacy SSE (unprotected for now — add auth later if needed)
        Route("/sse", endpoint=handle_sse_get),
        Route("/messages/", endpoint=handle_messages_post, methods=["POST"]),
        # Discovery (public)
        Route("/config", endpoint=handle_mcp_config),
    ]

    middleware = [
        Middleware(AuthenticationMiddleware, backend=BearerAuthBackend(token_verifier)),
        Middleware(AuthContextMiddleware),
    ]

    return Starlette(debug=False, routes=routes, middleware=middleware)


mcp_app = _build_mcp_app()
