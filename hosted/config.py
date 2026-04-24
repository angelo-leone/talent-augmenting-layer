"""Talent-Augmenting Layer -- Hosted App Configuration"""
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

# Google Drive export (Vanguard Pilot) — uses OAuth 2.0 user credentials
# so the app acts as you (bypasses IT restrictions on service accounts).
# Run `python -m hosted.gdrive_oauth_setup` once to obtain the refresh token.
# MCP OAuth 2.1 token lifetimes
MCP_ACCESS_TOKEN_EXPIRY = int(os.getenv("MCP_ACCESS_TOKEN_EXPIRY", "3600"))  # 1 hour
MCP_REFRESH_TOKEN_EXPIRY = int(os.getenv("MCP_REFRESH_TOKEN_EXPIRY", str(30 * 24 * 3600)))  # 30 days
MCP_AUTH_CODE_EXPIRY = int(os.getenv("MCP_AUTH_CODE_EXPIRY", "600"))  # 10 minutes

GDRIVE_OAUTH_CLIENT_ID = os.getenv("GDRIVE_OAUTH_CLIENT_ID", "")
GDRIVE_OAUTH_CLIENT_SECRET = os.getenv("GDRIVE_OAUTH_CLIENT_SECRET", "")
GDRIVE_OAUTH_REFRESH_TOKEN = os.getenv("GDRIVE_OAUTH_REFRESH_TOKEN", "")
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "")
PILOT_EXPORT_ENABLED = os.getenv("PILOT_EXPORT_ENABLED", "false").lower() == "true"

# Billing (Stripe) -- feature-flagged, off during the pilot.
# Set ENABLE_BILLING=true + STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET to
# activate. When off, /pricing returns 404 and billing columns on User
# stay at their defaults (plan_tier=free, no Stripe customer).
ENABLE_BILLING = os.getenv("ENABLE_BILLING", "false").lower() == "true"
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "")
STRIPE_PRICE_TEAM = os.getenv("STRIPE_PRICE_TEAM", "")
