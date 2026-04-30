"""Audit log helper.

Append-only recording of administrative and security-relevant actions.
Use ``record(...)`` from any handler that mutates state or makes a
permission decision worth keeping.

Action vocabulary (extend as needed):

  auth.login                   user signed in
  auth.logout                  user signed out
  auth.session_revoked         a session token was revoked
  org.invite_sent              admin sent an invite
  org.invite_revoked           admin revoked a pending invite
  org.invite_accepted          a recipient accepted an invite
  org.member_role_changed      admin changed a member's role
  profile.created              user finished an assessment
  profile.updated              user updated their profile
  profile.deleted              user deleted their profile
  profile.exported             user exported their profile
  account.deleted              user deleted their entire account
  admin.dashboard_viewed       admin opened the org dashboard
  admin.profile_viewed         admin viewed a member's profile
  oauth.token_issued           remote MCP issued a token
  oauth.token_revoked          remote MCP token revoked
  billing.subscription_changed plan tier changed (when billing is enabled)

Rows are append-only by convention. Do not write UPDATE or DELETE helpers
here; if you need redaction for GDPR purposes, write a separate, audited
purge function and log its execution as a fresh ``account.deleted`` row.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from hosted.database import AuditLog, async_session_factory

logger = logging.getLogger(__name__)


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    # X-Forwarded-For from Render's proxy (uvicorn started with --proxy-headers
    # makes this trustworthy; we still take the leftmost hop).
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _user_agent(request: Request | None) -> str | None:
    if request is None:
        return None
    ua = request.headers.get("user-agent")
    if ua and len(ua) > 512:
        return ua[:512]
    return ua


async def record(
    *,
    action: str,
    db: AsyncSession | None = None,
    actor_user_id: int | None = None,
    actor_email: str | None = None,
    org_id: int | None = None,
    target_type: str | None = None,
    target_id: str | int | None = None,
    request: Request | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Append a row to the audit log.

    Failures are logged but never raised: an audit-log write must not
    break the user request that triggered it. (Operationally, audit-log
    write failures are a P1 alert worth surfacing on a dashboard, but
    that is a follow-up and not in scope here.)

    If ``db`` is provided, the row is added to that session; the caller
    commits as part of their normal flow. Otherwise we open a short-lived
    session of our own. Pass ``db`` whenever you can, so the audit row
    commits atomically with the action it records.
    """
    target_id_str = str(target_id) if target_id is not None else None
    details_json = json.dumps(details, default=str) if details is not None else None

    row = AuditLog(
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        org_id=org_id,
        action=action,
        target_type=target_type,
        target_id=target_id_str,
        ip=_client_ip(request),
        user_agent=_user_agent(request),
        details_json=details_json,
    )

    try:
        if db is not None:
            db.add(row)
            return
        async with async_session_factory() as own:
            own.add(row)
            await own.commit()
    except Exception:
        logger.exception("audit_log.record failed for action=%s actor=%s", action, actor_user_id)
