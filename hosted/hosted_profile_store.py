"""Hosted (DB-backed) profile store for authenticated MCP requests.

When a user signs in via the OAuth flow and calls a TAOS MCP tool, the
auth context exposes their `user_id`. This store reads and writes their
profile against the hosted Postgres `profiles` table, scoped to that
single user. It mirrors `ProfileStore`'s API as async coroutines so the
tool handlers can swap between local and hosted stores transparently.

The hosted store is intentionally per-user: instantiate one per request,
not module-globally.

Anonymous requests (`MCP_REQUIRE_AUTH=false`, no Bearer token) keep using
the filesystem `ProfileStore`. The swap happens inside
`mcp-server/src/server.py:_get_active_store`.

Scope note: only the six profile-CRUD methods needed by the tool handlers
are implemented here. `log_interaction`, `get_skill_progression`, and
`get_org_summary` continue to use the filesystem store regardless of
auth state. Wiring those to the DB is a separate work item.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import select

from hosted.database import Profile as DBProfile, async_session_factory

# The domain `Profile` and parser live in mcp-server/src/profile_manager.
# We hand back parsed domain objects so tool handlers can read .calibration,
# .expertise, etc., without caring about the storage backend.
_server_src = Path(__file__).parent.parent / "mcp-server"
if str(_server_src) not in sys.path:
    sys.path.insert(0, str(_server_src))

if TYPE_CHECKING:
    from src.profile_manager import Profile as DomainProfile, ProfileStore


_NAME_RE = re.compile(r"\|\s*\*\*Name\*\*\s*\|\s*([^|]+)\s*\|")


def _extract_name(content: str) -> str | None:
    """Pull the user's display name out of the profile markdown.

    Profiles include an Identity Card row like `| **Name** | Angelo |`.
    Falls back to None if the row is missing or malformed.
    """
    m = _NAME_RE.search(content)
    return m.group(1).strip() if m else None


class HostedProfileStore:
    """Profile store backed by the hosted Postgres DB, scoped to one user.

    All methods mirror `ProfileStore`'s sync API as async coroutines.
    The `name` argument is accepted for parity but is ignored for lookup:
    the user_id is the real key. A user has at most one active profile
    (highest `version`); writes bump the version rather than overwrite,
    keeping history in the DB.
    """

    def __init__(self, user_id: int, parser: "ProfileStore"):
        self.user_id = user_id
        self._parser = parser

    async def list_profiles(self) -> list[str]:
        """Return [user's name] if they have a profile, [] otherwise."""
        async with async_session_factory() as db:
            stmt = (
                select(DBProfile.content_md)
                .where(DBProfile.user_id == self.user_id)
                .order_by(DBProfile.version.desc())
                .limit(1)
            )
            content = (await db.execute(stmt)).scalar_one_or_none()
        if not content:
            return []
        return [_extract_name(content) or f"User {self.user_id}"]

    async def profile_exists(self, name: str) -> bool:
        async with async_session_factory() as db:
            stmt = (
                select(DBProfile.id)
                .where(DBProfile.user_id == self.user_id)
                .limit(1)
            )
            return (await db.execute(stmt)).scalar_one_or_none() is not None

    async def read_profile_raw(self, name: str) -> str | None:
        async with async_session_factory() as db:
            stmt = (
                select(DBProfile.content_md)
                .where(DBProfile.user_id == self.user_id)
                .order_by(DBProfile.version.desc())
                .limit(1)
            )
            return (await db.execute(stmt)).scalar_one_or_none()

    async def write_profile_raw(
        self,
        name: str,
        content: str,
        scores_json: str | None = None,
    ) -> str:
        """Insert a new Profile row at the next version number for this user.

        `scores_json` is a JSON-serialized blob matching the web flow's
        `scores_storage` shape (scores, calibration, domain_ratings,
        skills_to_develop, skills_to_protect, career_goals). The web
        dashboard reads it to render charts. When None, carry the previous
        version's scores_json forward so a markdown-only edit via
        `talent_save_profile` does not blank the dashboard.

        Returns an opaque identifier string so the caller can echo "saved"
        without leaking DB internals.
        """
        async with async_session_factory() as db:
            current = await db.execute(
                select(DBProfile.version, DBProfile.scores_json)
                .where(DBProfile.user_id == self.user_id)
                .order_by(DBProfile.version.desc())
                .limit(1)
            )
            prev = current.first()
            if prev is not None:
                current_version, prev_scores_json = prev
            else:
                current_version, prev_scores_json = 0, None
            row = DBProfile(
                user_id=self.user_id,
                version=current_version + 1,
                content_md=content,
                scores_json=(scores_json if scores_json is not None else (prev_scores_json or "{}")),
            )
            db.add(row)
            await db.commit()
            return f"db://profiles/user/{self.user_id}/v{row.version}"

    async def read_profile(self, name: str) -> "DomainProfile | None":
        raw = await self.read_profile_raw(name)
        if not raw:
            return None
        # The local ProfileStore's parser is pure logic; reusing it keeps
        # the domain object shape identical across storage backends.
        return self._parser._parse_profile(name, raw)

    async def delete_profile(self, name: str) -> bool:
        async with async_session_factory() as db:
            stmt = select(DBProfile).where(DBProfile.user_id == self.user_id)
            rows = (await db.execute(stmt)).scalars().all()
            if not rows:
                return False
            for row in rows:
                await db.delete(row)
            await db.commit()
            return True
