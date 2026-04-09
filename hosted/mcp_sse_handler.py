"""
MCP SSE Transport Handler for Remote Access

Integrates the Talent-Augmenting Layer MCP server with FastAPI via SSE,
allowing remote clients (Claude Code, Claude Desktop, Cursor, etc.) to connect.

Architecture:
  1. Starlette sub-app mounted at /mcp on the FastAPI host
  2. GET  /mcp/sse       — client opens persistent SSE stream here
  3. POST /mcp/messages/  — client sends JSON-RPC messages here
  4. The SseServerTransport from the MCP SDK bridges these two

All MCP tools (scoring, classification, profile CRUD, logging) are pure Python —
no LLM API keys are needed on the server side.  The client's own LLM model
(Claude Code, Cursor, etc.) drives the conversation; the MCP server only
provides tools, resources, and prompts.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

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
# SSE transport — single instance shared across connections
# The endpoint path must match the POST route below (relative to /mcp mount).
# ---------------------------------------------------------------------------

_sse_transport = SseServerTransport("/messages/")


# ---------------------------------------------------------------------------
# Route handlers (ASGI-level — Starlette passes scope/receive/send)
# ---------------------------------------------------------------------------

async def handle_sse_get(request: Request):
    """
    GET /mcp/sse — client opens a persistent Server-Sent Events stream.

    The MCP SDK's ``connect_sse`` context manager:
      • sends an initial SSE event telling the client where to POST messages
      • yields (read_stream, write_stream) used by the MCP server
      • keeps the SSE connection open for streaming responses back
    """
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
    """
    POST /mcp/messages/ — client sends JSON-RPC messages here.

    The SSE transport correlates each POST to the right SSE stream
    using a session_id query parameter added automatically by the client.
    """
    await _sse_transport.handle_post_message(
        request.scope, request.receive, request._send
    )


async def handle_mcp_config(request: Request):
    """
    GET /mcp/config — return client configuration JSON.

    Clients can fetch this to auto-configure their MCP settings.
    """
    app_url = os.environ.get("APP_URL", "https://proworker-hosted.onrender.com")
    return JSONResponse(
        {
            "type": "sse",
            "url": f"{app_url}/mcp/sse",
            "description": "Talent-Augmenting Layer — Remote MCP Server",
            "note": (
                "All tools are pure Python — no API keys needed on the server. "
                "Your Claude Code / Cursor model drives the conversation."
            ),
            "documentation": "https://github.com/angelo-leone/talent-augmenting-layer#remote-mcp-configuration",
            "supported_clients": [
                "Claude Code",
                "Claude Desktop",
                "Cursor",
                "Any MCP-compatible IDE",
            ],
        }
    )


# ---------------------------------------------------------------------------
# Starlette sub-app — mount this on the FastAPI host at /mcp
# ---------------------------------------------------------------------------

mcp_app = Starlette(
    debug=False,
    routes=[
        Route("/sse", endpoint=handle_sse_get),
        Route("/messages/", endpoint=handle_messages_post, methods=["POST"]),
        Route("/config", endpoint=handle_mcp_config),
    ],
)
