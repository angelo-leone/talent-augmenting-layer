"""
Talent-Augmenting Layer — Organisation Dashboard

Streamlit dashboard for org-level workforce augmentation analytics.
Tracks: dependency risk, skill progression, de-skilling alerts, engagement trends.

Run: streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

# Add mcp-server to path so we can import profile_manager
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server"))

import streamlit as st
import json

from src.profile_manager import ProfileStore

# ── Config ───────────────────────────────────────────────────────────────────

PROFILES_DIR = Path(__file__).parent.parent / "profiles"
store = ProfileStore(PROFILES_DIR)


# ── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Talent-Augmenting Layer — Org Dashboard",
    page_icon="🎯",
    layout="wide",
)

st.title("Talent-Augmenting Layer — Organisation Dashboard")
st.markdown("*Workforce augmentation analytics. Track skill growth, dependency risk, and de-skilling.*")

# ── Load Data ────────────────────────────────────────────────────────────────

summary = store.get_org_summary()

if "message" in summary and summary.get("total_profiles", 0) == 0:
    st.warning("No profiles found. Run `/talent-assess` for team members to populate the dashboard.")
    st.stop()

profiles = summary["profiles"]
org_avg = summary["org_averages"]
alerts = summary["alerts"]
domain_summary = summary["domain_summary"]


# ── Top-Level Metrics ────────────────────────────────────────────────────────

st.header("Organisation Overview")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Profiles", summary["total_profiles"])

with col2:
    risk_color = "🟢" if org_avg["dependency_risk"] < 4 else "🟡" if org_avg["dependency_risk"] < 7 else "🔴"
    st.metric("Avg Dependency Risk", f"{org_avg['dependency_risk']}/10 {risk_color}")

with col3:
    gp_color = "🟢" if org_avg["growth_potential"] > 6 else "🟡" if org_avg["growth_potential"] > 3 else "🔴"
    st.metric("Avg Growth Potential", f"{org_avg['growth_potential']}/10 {gp_color}")

with col4:
    st.metric("Avg Expertise", f"{org_avg['expertise']}/5")

with col5:
    alert_count = alerts["at_risk_count"] + alerts["declining_trend_count"]
    alert_color = "🟢" if alert_count == 0 else "🟡" if alert_count < 3 else "🔴"
    st.metric("Active Alerts", f"{alert_count} {alert_color}")


# ── Alerts ───────────────────────────────────────────────────────────────────

if alerts["at_risk_count"] > 0 or alerts["declining_trend_count"] > 0 or alerts["total_atrophy_warnings"] > 0:
    st.header("Alerts")

    if alerts["at_risk_count"] > 0:
        at_risk = [p["name"] for p in profiles if p["dependency_risk"] >= 7]
        st.error(f"**High Dependency Risk** ({alerts['at_risk_count']} people): {', '.join(at_risk)}")

    if alerts["declining_trend_count"] > 0:
        declining = [p["name"] for p in profiles if p["trend_direction"] == "declining"]
        st.warning(f"**Declining Engagement Trend** ({alerts['declining_trend_count']} people): {', '.join(declining)}")

    if alerts["total_atrophy_warnings"] > 0:
        atrophy_people = [(p["name"], p["atrophy_warnings"]) for p in profiles if p["atrophy_warnings"]]
        for name, domains in atrophy_people:
            st.warning(f"**Atrophy Risk**: {name} — domains: {', '.join(domains)}")


# ── Individual Profiles ──────────────────────────────────────────────────────

st.header("Individual Profiles")

for p in sorted(profiles, key=lambda x: x["dependency_risk"], reverse=True):
    with st.expander(f"**{p['name']}** — {p.get('role', 'No role')} | Risk: {p['dependency_risk']}/10 | Growth: {p['growth_potential']}/10"):
        pcol1, pcol2 = st.columns(2)

        with pcol1:
            st.subheader("Expertise Map")
            for domain, rating in p["expertise_by_domain"].items():
                bar_fill = "█" * rating + "░" * (5 - rating)
                label = {1: "Novice", 2: "Developing", 3: "Proficient", 4: "Advanced", 5: "Expert"}.get(rating, "?")
                st.text(f"  {bar_fill} {rating}/5 {label} — {domain}")

        with pcol2:
            st.subheader("Tracking")
            st.text(f"  Total interactions: {p['total_interactions']}")
            st.text(f"  Passive ratio: {p['passive_ratio']:.0%}")
            st.text(f"  Trend: {p['trend_direction']}")
            st.text(f"  Friction level: {p['friction_level']}")
            if p["atrophy_warnings"]:
                st.text(f"  Atrophy warnings: {', '.join(p['atrophy_warnings'])}")


# ── Domain Analysis ──────────────────────────────────────────────────────────

st.header("Organisation-Wide Skill Distribution")

if domain_summary:
    # Sort by average rating
    sorted_domains = sorted(domain_summary.items(), key=lambda x: x[1]["avg"])

    for domain, stats in sorted_domains:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            bar_len = int(stats["avg"] * 10)
            bar = "█" * bar_len + "░" * (50 - bar_len)
            st.text(f"  {bar} {stats['avg']}/5 — {domain}")
        with col_b:
            st.text(f"  Range: {stats['min']}-{stats['max']} | n={stats['count']}")


# ── Footer ───────────────────────────────────────────────────────────────────

st.divider()
st.markdown(
    "*Talent-Augmenting Layer — Making workers better, not dependent. "
    "Powered by research from Bucinca, Acemoglu, Mollick.*"
)
