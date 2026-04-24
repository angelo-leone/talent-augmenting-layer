"""Org-scoped aggregation for the admin dashboard.

Mirrors mcp-server/src/profile_manager.py:ProfileStore.get_org_summary but
pulls from the hosted Postgres database and constrains to a single org_id.
Admins only see members of their own org.
"""
from __future__ import annotations

import datetime
import json
import logging
from collections import defaultdict
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from hosted.database import (
    Profile,
    User,
    Organization,
    ChatLog,
    EngagementLevel,
    SkillSignal,
)

logger = logging.getLogger(__name__)


async def get_org_summary_scoped(org_id: int, db: AsyncSession) -> dict[str, Any]:
    """Return aggregate stats for all members of `org_id`.

    Shape matches the MCP-server org-summary output loosely: org_averages,
    alerts, domain_summary, profiles. Fields drawn from each member's latest
    Profile row and recent ChatLog telemetry.
    """
    # 1. Load org + members
    org_result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_result.scalar_one_or_none()
    if org is None:
        return {"error": "Organization not found", "profiles": []}

    members_result = await db.execute(select(User).where(User.org_id == org_id))
    members = members_result.scalars().all()
    if not members:
        return {
            "org": {"id": org.id, "name": org.name, "slug": org.slug},
            "total_profiles": 0,
            "profiles": [],
            "message": "No members in this org yet.",
        }

    # 2. Latest profile per member
    member_ids = [m.id for m in members]
    latest_version_subq = (
        select(Profile.user_id, func.max(Profile.version).label("max_version"))
        .where(Profile.user_id.in_(member_ids))
        .group_by(Profile.user_id)
        .subquery()
    )
    latest_profiles_result = await db.execute(
        select(Profile).join(
            latest_version_subq,
            (Profile.user_id == latest_version_subq.c.user_id)
            & (Profile.version == latest_version_subq.c.max_version),
        )
    )
    latest_profiles = {p.user_id: p for p in latest_profiles_result.scalars().all()}

    # 3. Recent chat-log engagement signals (last 30 days)
    thirty_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)
    recent_logs_result = await db.execute(
        select(ChatLog).where(
            ChatLog.user_id.in_(member_ids),
            ChatLog.created_at >= thirty_days_ago,
        )
    )
    recent_logs = recent_logs_result.scalars().all()
    logs_by_user: dict[int, list[ChatLog]] = defaultdict(list)
    for log in recent_logs:
        logs_by_user[log.user_id].append(log)

    profiles_data: list[dict[str, Any]] = []
    all_domains: dict[str, list[int]] = defaultdict(list)
    at_risk_count = 0
    atrophy_count = 0
    declining_count = 0

    for member in members:
        profile = latest_profiles.get(member.id)
        member_logs = logs_by_user.get(member.id, [])

        scores: dict[str, Any] = {}
        domain_ratings: dict[str, int] = {}
        if profile:
            try:
                scores = json.loads(profile.scores_json) or {}
            except (json.JSONDecodeError, TypeError):
                scores = {}
            # domain ratings are keyed under "esa_ratings" or "domain_ratings"
            # depending on when the profile was written. Check both.
            raw_domains = scores.get("domain_ratings") or scores.get("esa_ratings") or {}
            if isinstance(raw_domains, dict):
                for domain, rating in raw_domains.items():
                    try:
                        r = int(rating)
                    except (TypeError, ValueError):
                        continue
                    domain_ratings[domain] = r
                    all_domains[domain].append(r)

        # Engagement metrics from chat logs
        total_interactions = len(member_logs)
        passive_count = sum(
            1 for log in member_logs if log.engagement_level == EngagementLevel.passive
        )
        atrophy_logs = sum(
            1 for log in member_logs if log.skill_signal == SkillSignal.atrophy
        )
        growth_logs = sum(
            1 for log in member_logs if log.skill_signal == SkillSignal.growth
        )
        passive_ratio = passive_count / total_interactions if total_interactions else 0.0

        dependency_risk = _extract_number(scores, "adr", "dependency_risk", "dependency_risk_score")
        growth_potential = _extract_number(scores, "gp", "growth_potential", "growth_potential_score")

        trend_direction = "no_data"
        if total_interactions >= 5:
            if atrophy_logs > growth_logs:
                trend_direction = "declining"
                declining_count += 1
            elif growth_logs > atrophy_logs:
                trend_direction = "improving"
            else:
                trend_direction = "stable"

        if dependency_risk >= 7:
            at_risk_count += 1
        if atrophy_logs >= 3:
            atrophy_count += 1

        expertise_vals = list(domain_ratings.values())
        avg_expertise = sum(expertise_vals) / len(expertise_vals) if expertise_vals else 0.0

        profiles_data.append({
            "user_id": member.id,
            "name": member.name or member.email,
            "email": member.email,
            "role": str(member.role.value) if member.role else "member",
            "has_profile": profile is not None,
            "profile_version": profile.version if profile else None,
            "last_updated": profile.created_at.isoformat() if profile else None,
            "expertise_avg": round(avg_expertise, 1),
            "expertise_count": len(expertise_vals),
            "expertise_by_domain": domain_ratings,
            "dependency_risk": dependency_risk,
            "growth_potential": growth_potential,
            "total_interactions": total_interactions,
            "passive_ratio": round(passive_ratio, 2),
            "atrophy_signals_30d": atrophy_logs,
            "growth_signals_30d": growth_logs,
            "trend_direction": trend_direction,
        })

    total_profiles = sum(1 for p in profiles_data if p["has_profile"])
    if total_profiles == 0:
        org_averages = {"dependency_risk": 0, "growth_potential": 0, "expertise": 0}
    else:
        org_averages = {
            "dependency_risk": round(
                sum(p["dependency_risk"] for p in profiles_data if p["has_profile"]) / total_profiles, 1
            ),
            "growth_potential": round(
                sum(p["growth_potential"] for p in profiles_data if p["has_profile"]) / total_profiles, 1
            ),
            "expertise": round(
                sum(p["expertise_avg"] for p in profiles_data if p["has_profile"]) / total_profiles, 1
            ),
        }

    domain_summary = {
        domain: {
            "avg": round(sum(ratings) / len(ratings), 1),
            "min": min(ratings),
            "max": max(ratings),
            "count": len(ratings),
        }
        for domain, ratings in all_domains.items()
    }

    return {
        "org": {"id": org.id, "name": org.name, "slug": org.slug},
        "member_count": len(members),
        "total_profiles": total_profiles,
        "org_averages": org_averages,
        "alerts": {
            "at_risk_count": at_risk_count,        # dependency_risk >= 7
            "declining_trend_count": declining_count,
            "atrophy_signal_members": atrophy_count,  # >= 3 atrophy logs in 30d
        },
        "domain_summary": domain_summary,
        "profiles": profiles_data,
    }


def _extract_number(scores: dict[str, Any], *keys: str) -> float:
    """Try each key; return 0 if none yield a number."""
    for key in keys:
        val = scores.get(key)
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, dict):
            inner = val.get("score") or val.get("value")
            if isinstance(inner, (int, float)):
                return float(inner)
    return 0.0
