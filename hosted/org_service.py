"""Org-scoped aggregation for the admin dashboard.

Mirrors mcp-server/src/profile_manager.py:ProfileStore.get_org_summary but
pulls from the hosted Postgres database and constrains to a single org_id.
Admins only see members of their own org.

PRIVACY POSTURE (aggregate-only employer view)
----------------------------------------------
The employer/org view is deliberately aggregate-only. An org admin never sees
any individual worker's skill ratings, dependency-risk score, trend, or
atrophy signals. Per-member metrics are computed here ONLY to build org-level
aggregates and are never returned. Two k-anonymity floors apply so that no
aggregate can single out an individual in a small team:

  * MIN_AGGREGATE_GROUP : minimum onboarded profiles before any average /
    distribution / domain stat is exposed at all.
  * MIN_SENSITIVE_GROUP : higher floor for the risk and atrophy alert counts,
    which are the most monitoring-flavoured numbers.

Individual data remains visible only to the member themselves (their own
dashboard). This is what keeps the deployment on Solita's "light" risk path
and out of the EU AI Act employment (Annex III) category: the system does not
monitor or evaluate any identifiable individual for the employer.

NOTE: research/pilot data (e.g. an RCT) is a SEPARATE processing activity. It
draws on the raw Profile/ChatLog tables under explicit participant consent and
a data-sharing agreement, not on this employer view. Keep the two flows
distinct: this function must never become the research export path.
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
    SkillSignal,
)

logger = logging.getLogger(__name__)

# k-anonymity floors for the employer view. Tune here if Solita (or another
# customer) requires a different threshold; some prefer 10 across the board for
# employee data. Split default: 5 for skill aggregates, 10 for risk/atrophy.
MIN_AGGREGATE_GROUP = 5
MIN_SENSITIVE_GROUP = 10


async def get_org_summary_scoped(org_id: int, db: AsyncSession) -> dict[str, Any]:
    """Return aggregate-only stats for all members of `org_id`.

    No per-individual skill, risk, trend, or atrophy data is ever returned.
    Aggregates are suppressed below the k-anonymity floors above.
    """
    # 1. Load org + members
    org_result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_result.scalar_one_or_none()
    if org is None:
        return {"error": "Organization not found", "members": []}

    members_result = await db.execute(select(User).where(User.org_id == org_id))
    members = members_result.scalars().all()
    if not members:
        return {
            "org": {"id": org.id, "name": org.name, "slug": org.slug},
            "member_count": 0,
            "total_profiles": 0,
            "members": [],
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

    # 4. Per-member metrics computed ONLY to feed org-level aggregates.
    #    None of this is returned at the individual level.
    all_domains: dict[str, list[int]] = defaultdict(list)
    dep_risks: list[float] = []
    growth_potentials: list[float] = []
    expertise_avgs: list[float] = []
    risk_buckets = {"low": 0, "medium": 0, "high": 0, "none": 0}
    at_risk_count = 0
    atrophy_count = 0
    declining_count = 0
    onboarded_count = 0

    # Identity/role only, for org administration (invite, assign roles). No
    # skill, risk, behaviour, or onboarding-status data per person.
    members_admin: list[dict[str, Any]] = [
        {
            "name": m.name or m.email,
            "email": m.email,
            "role": str(m.role.value) if m.role else "member",
        }
        for m in members
    ]

    for member in members:
        profile = latest_profiles.get(member.id)
        member_logs = logs_by_user.get(member.id, [])

        if not profile:
            risk_buckets["none"] += 1
            continue
        onboarded_count += 1

        scores: dict[str, Any] = {}
        try:
            scores = json.loads(profile.scores_json) or {}
        except (json.JSONDecodeError, TypeError):
            scores = {}

        raw_domains = scores.get("domain_ratings") or scores.get("esa_ratings") or {}
        domain_ratings: dict[str, int] = {}
        if isinstance(raw_domains, dict):
            for domain, rating in raw_domains.items():
                try:
                    r = int(rating)
                except (TypeError, ValueError):
                    continue
                domain_ratings[domain] = r
                all_domains[domain].append(r)

        total_interactions = len(member_logs)
        atrophy_logs = sum(
            1 for log in member_logs if log.skill_signal == SkillSignal.atrophy
        )
        growth_logs = sum(
            1 for log in member_logs if log.skill_signal == SkillSignal.growth
        )

        dependency_risk = _extract_number(scores, "adr", "dependency_risk", "dependency_risk_score")
        growth_potential = _extract_number(scores, "gp", "growth_potential", "growth_potential_score")
        dep_risks.append(dependency_risk)
        growth_potentials.append(growth_potential)

        expertise_vals = list(domain_ratings.values())
        if expertise_vals:
            expertise_avgs.append(sum(expertise_vals) / len(expertise_vals))

        # Aggregate risk-tier distribution (counts only).
        if dependency_risk >= 7:
            risk_buckets["high"] += 1
            at_risk_count += 1
        elif dependency_risk >= 4:
            risk_buckets["medium"] += 1
        else:
            risk_buckets["low"] += 1

        if atrophy_logs >= 3:
            atrophy_count += 1
        if total_interactions >= 5 and atrophy_logs > growth_logs:
            declining_count += 1

    total_profiles = onboarded_count

    # 5. Apply k-anonymity floors before exposing anything.
    base_ok = total_profiles >= MIN_AGGREGATE_GROUP
    sensitive_ok = total_profiles >= MIN_SENSITIVE_GROUP

    org_averages = None
    risk_distribution = None
    if base_ok:
        org_averages = {
            "dependency_risk": round(sum(dep_risks) / len(dep_risks), 1) if dep_risks else 0,
            "growth_potential": round(sum(growth_potentials) / len(growth_potentials), 1) if growth_potentials else 0,
            "expertise": round(sum(expertise_avgs) / len(expertise_avgs), 1) if expertise_avgs else 0,
        }
        risk_distribution = dict(risk_buckets)

    # Domain summary: only domains rated by at least MIN_AGGREGATE_GROUP
    # members, and only avg + count (min/max would expose the extreme person).
    domain_summary = {
        domain: {"avg": round(sum(ratings) / len(ratings), 1), "count": len(ratings)}
        for domain, ratings in all_domains.items()
        if len(ratings) >= MIN_AGGREGATE_GROUP
    }

    # Risk/atrophy alerts only above the higher (sensitive) floor.
    alerts = None
    if sensitive_ok:
        alerts = {
            "at_risk_count": at_risk_count,
            "declining_trend_count": declining_count,
            "atrophy_signal_members": atrophy_count,
        }

    return {
        "org": {"id": org.id, "name": org.name, "slug": org.slug},
        "member_count": len(members),
        "total_profiles": total_profiles,
        "onboarded_count": onboarded_count,
        "aggregate_suppressed": not base_ok,
        "min_group": MIN_AGGREGATE_GROUP,
        "min_sensitive_group": MIN_SENSITIVE_GROUP,
        "org_averages": org_averages,
        "risk_distribution": risk_distribution,
        "alerts": alerts,
        "domain_summary": domain_summary,
        "members": members_admin,
        # No per-individual skill/risk/behaviour data is returned, by design.
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
