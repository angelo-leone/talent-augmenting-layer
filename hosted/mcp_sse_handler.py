"""
MCP Remote Transport Handler

Exposes the Talent-Augmenting Layer MCP server over HTTP so remote clients
(Claude Code, Claude Desktop, Cursor, etc.) can connect.

Two transports are provided:

  **Streamable HTTP** (primary — what modern MCP clients use):
    - All methods on a single endpoint: POST/GET/DELETE /mcp
    - Stateless — no long-lived connections needed
    - Claude Desktop (2025+), Claude Code, and Cursor use this

  **SSE** (legacy — for older clients):
    - GET  /mcp/sse        — persistent SSE stream
    - POST /mcp/messages/   — JSON-RPC message delivery

All MCP tools are pure Python — no LLM API keys on the server.
The client's own model drives the conversation.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

logger = logging.getLogger(__name__)

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
# Config endpoint
# ---------------------------------------------------------------------------

async def handle_mcp_config(request: Request):
    """GET /mcp/config — return client configuration JSON."""
    app_url = os.environ.get("APP_URL", "https://proworker-hosted.onrender.com")
    return JSONResponse(
        {
            "type": "streamable-http",
            "url": f"{app_url}/mcp",
            "legacy_sse_url": f"{app_url}/mcp/sse",
            "description": "Talent-Augmenting Layer — Remote MCP Server",
            "note": (
                "All tools are pure Python — no API keys needed on the server. "
                "Your Claude Code / Cursor model drives the conversation."
            ),
            "documentation": "https://github.com/angelo-leone/talent-augmenting-layer#remote-mcp-configuration",
        }
    )


# ---------------------------------------------------------------------------
# Starlette sub-app — mount on the FastAPI host at /mcp
#
# Route priority:
#   POST/GET/DELETE /mcp      → Streamable HTTP (primary)
#   GET             /mcp/sse  → SSE stream (legacy)
#   POST            /mcp/messages/ → SSE messages (legacy)
#   GET             /mcp/config    → discovery
#
# NOTE: The session manager lifecycle is managed by the parent FastAPI app
# (in app.py lifespan), NOT by this sub-app. This avoids issues with
# sub-app lifespans not being invoked by certain FastAPI/Starlette versions.
# ---------------------------------------------------------------------------


async def _streamable_http_asgi(scope, receive, send):
    """ASGI wrapper that lazily delegates to the session manager."""
    mgr = get_session_manager()
    await mgr.handle_request(scope, receive, send)


mcp_app = Starlette(
    debug=False,
    routes=[
        # Legacy SSE (must be before the catch-all mount)
        Route("/sse", endpoint=handle_sse_get),
        Route("/messages/", endpoint=handle_messages_post, methods=["POST"]),
        # Discovery
        Route("/config", endpoint=handle_mcp_config),
        # Streamable HTTP — catch-all for GET/POST/DELETE on root
        Mount("/", app=_streamable_http_asgi),
    ],
)
