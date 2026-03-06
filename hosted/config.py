"""Pro Worker AI -- Hosted App Configuration"""
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
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@proworker.ai")

# App
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")
CHECKIN_INTERVAL_DAYS = int(os.getenv("CHECKIN_INTERVAL_DAYS", "14"))
