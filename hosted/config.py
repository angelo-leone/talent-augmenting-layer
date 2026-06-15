"""Talent-Augmenting OS: Hosted App Configuration"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
MCP_SERVER_DIR = PROJECT_ROOT / "mcp-server"

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'proworker.db'}")

# Render provides postgres:// URLs, but SQLAlchemy 2.0 requires postgresql://
# Also needs +asyncpg driver for async support
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# LLM API
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")  # "anthropic", "openai", or "gemini"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")  # For Gemini
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")  # or "claude-sonnet-4-20250514" or "gpt-4o"

# Email (SendGrid)
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@talent-layer.local")

# App
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")
CHECKIN_INTERVAL_DAYS = int(os.getenv("CHECKIN_INTERVAL_DAYS", "14"))

# Google Drive export (Vanguard Pilot): uses OAuth 2.0 user credentials
# so the app acts as you (bypasses IT restrictions on service accounts).
# Run `python -m hosted.gdrive_oauth_setup` once to obtain the refresh token.
# MCP OAuth 2.1 token lifetimes
MCP_ACCESS_TOKEN_EXPIRY = int(os.getenv("MCP_ACCESS_TOKEN_EXPIRY", "3600"))  # 1 hour
MCP_REFRESH_TOKEN_EXPIRY = int(os.getenv("MCP_REFRESH_TOKEN_EXPIRY", str(30 * 24 * 3600)))  # 30 days
MCP_AUTH_CODE_EXPIRY = int(os.getenv("MCP_AUTH_CODE_EXPIRY", "600"))  # 10 minutes

# MCP authentication enforcement.
#
# When False (default) the /mcp Streamable HTTP and /mcp/sse endpoints accept
# anonymous requests for backward compatibility with the existing Vanguard
# pilot installs (some of which are still configured against an open endpoint
# as of mid-May 2026).
#
# When True every MCP request must arrive with a valid Bearer token.
# BearerAuthBackend (Starlette AuthenticationMiddleware) already populates
# request.user from the token; this flag turns the missing-token case from a
# silent pass-through into a 401.
#
# Flip to True once the Vanguard pilot has ended and all pilot users have
# either migrated to the OAuth flow or signed out.
MCP_REQUIRE_AUTH = os.getenv("MCP_REQUIRE_AUTH", "false").lower() == "true"

# When True the MCP server sends the TAOS system prompt as
# `initialize.instructions` on every connect, giving ambient TAOS coaching
# without the user invoking a skill. Default False during the pilot
# wind-down so existing pilot users see no behaviour change. Flip to True
# on the deployment once the pilot has closed.
#
# The flag is read directly inside `mcp-server/src/server.py:_load_server_instructions`
# (stdio installs do not import this module); this entry exists for
# operational visibility and parity with MCP_REQUIRE_AUTH.
MCP_SEND_INSTRUCTIONS = os.getenv("MCP_SEND_INSTRUCTIONS", "false").lower() == "true"

GDRIVE_OAUTH_CLIENT_ID = os.getenv("GDRIVE_OAUTH_CLIENT_ID", "")
GDRIVE_OAUTH_CLIENT_SECRET = os.getenv("GDRIVE_OAUTH_CLIENT_SECRET", "")
GDRIVE_OAUTH_REFRESH_TOKEN = os.getenv("GDRIVE_OAUTH_REFRESH_TOKEN", "")
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "")
PILOT_EXPORT_ENABLED = os.getenv("PILOT_EXPORT_ENABLED", "false").lower() == "true"

# Billing (Stripe): feature-flagged, off during the pilot.
# Set ENABLE_BILLING=true + STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET to
# activate. When off, /pricing returns 404 and billing columns on User
# stay at their defaults (plan_tier=free, no Stripe customer).
ENABLE_BILLING = os.getenv("ENABLE_BILLING", "false").lower() == "true"
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "")
STRIPE_PRICE_TEAM = os.getenv("STRIPE_PRICE_TEAM", "")

# Reveal → free-trial funnel: feature-flagged, off during the pilot.
# When True, a completed assessment routes the user to /reveal (a teaser of
# their scores) and the full /dashboard unlocks only after they start a
# 30-day free trial (one click, NO payment, NO card). When False (default)
# the assessment goes straight to /dashboard exactly as before, so existing
# pilot users see no change. Flip to true at launch, after the pilot closes.
ENABLE_TRIAL_GATE = os.getenv("ENABLE_TRIAL_GATE", "false").lower() == "true"
TRIAL_DAYS = int(os.getenv("TRIAL_DAYS", "30"))

# Accounts that always get full access: never shown the reveal gate, never asked
# to pay. Comma-separated emails; defaults to the founder.
FULL_ACCESS_EMAILS = {
    e.strip().lower()
    for e in os.getenv("FULL_ACCESS_EMAILS", "angelo.leone1204@gmail.com").split(",")
    if e.strip()
}
# Grandfather: accounts created before this ISO datetime are never gated. Set it
# to the moment the trial gate is switched on so existing users keep full access.
TRIAL_GATE_SINCE = os.getenv("TRIAL_GATE_SINCE", "")
