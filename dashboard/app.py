"""
Talent-Augmenting OS: Organisation Dashboard

Streamlit dashboard for org-level workforce augmentation analytics.
Aggregate-only by design: no individual worker's skill, risk, or trend data is
ever shown. Numbers appear only above k-anonymity floors so no individual can
be identified. Individual data is private to each member.

Run: streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

# Add mcp-server to path so we can import profile_manager
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server"))

import streamlit as st

from src.profile_manager import ProfileStore

# ── Config ───────────────────────────────────────────────────────────────────

PROFILES_DIR = Path(__file__).parent.parent / "profiles"
store = ProfileStore(PROFILES_DIR)


# ── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Talent-Augmenting OS: Org Dashboard",
    page_icon="🎯",
    layout="wide",
)

st.title("Talent-Augmenting OS: Organisation Dashboard")
st.markdown("*Aggregate-only workforce analytics. Individual skill, risk, and trend data stays private to each member.*")

# ── Load Data ────────────────────────────────────────────────────────────────

summary = store.get_org_summary()

if summary.get("total_profiles", 0) == 0:
    st.warning("No profiles found. Run `/talent-assess` for team members to populate the dashboard.")
    st.stop()

min_group = summary.get("min_group", 5)
min_sensitive = summary.get("min_sensitive_group", 10)

st.caption(
    f"Aggregate numbers appear once at least {min_group} members have onboarded "
    f"(risk and atrophy figures at {min_sensitive}), so no individual can be identified."
)

if summary.get("aggregate_suppressed"):
    st.info(
        f"Not enough onboarded members yet to show aggregates without risking identifying someone. "
        f"This view unlocks at {min_group} onboarded members "
        f"({summary.get('total_profiles', 0)} so far)."
    )
    st.stop()

org_avg = summary["org_averages"]
alerts = summary.get("alerts")
domain_summary = summary.get("domain_summary", {})


# ── Top-Level Metrics ────────────────────────────────────────────────────────

st.header("Organisation Overview")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Onboarded Profiles", summary["total_profiles"])

with col2:
    risk_color = "🟢" if org_avg["dependency_risk"] < 4 else "🟡" if org_avg["dependency_risk"] < 7 else "🔴"
    st.metric("Avg Dependency Risk", f"{org_avg['dependency_risk']}/10 {risk_color}")

with col3:
    gp_color = "🟢" if org_avg["growth_potential"] > 6 else "🟡" if org_avg["growth_potential"] > 3 else "🔴"
    st.metric("Avg Growth Potential", f"{org_avg['growth_potential']}/10 {gp_color}")

with col4:
    st.metric("Avg Expertise", f"{org_avg['expertise']}/5")

with col5:
    if alerts:
        alert_count = alerts["at_risk_count"] + alerts["declining_trend_count"]
        alert_color = "🟢" if alert_count == 0 else "🟡" if alert_count < 3 else "🔴"
        st.metric("Active Alerts", f"{alert_count} {alert_color}")
    else:
        st.metric("Active Alerts", "—")


# ── Alerts (counts only, no names) ─────────────────────────────────────────────

st.header("Alerts")
if not alerts:
    st.caption(f"Risk and atrophy figures unlock at {min_sensitive} onboarded members.")
else:
    acol1, acol2, acol3 = st.columns(3)
    with acol1:
        st.metric("High dependency risk (ADR ≥ 7)", alerts["at_risk_count"])
    with acol2:
        st.metric("Declining 30-day trend", alerts["declining_trend_count"])
    with acol3:
        st.metric("Members with ≥3 atrophy signals (30d)", alerts["atrophy_signal_members"])
    st.caption("Counts only. Which members these are is private to each member and not shown here.")


# ── Domain Analysis (aggregate) ────────────────────────────────────────────────

st.header("Organisation-Wide Skill Distribution")

if domain_summary:
    st.caption(f"Only domains rated by at least {min_group} members are shown.")
    sorted_domains = sorted(domain_summary.items(), key=lambda x: x[1]["avg"])
    for domain, stats in sorted_domains:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            bar_len = int(stats["avg"] * 10)
            bar = "█" * bar_len + "░" * (50 - bar_len)
            st.text(f"  {bar} {stats['avg']}/5: {domain}")
        with col_b:
            st.text(f"  n={stats['count']}")
else:
    st.caption(f"No domain has yet been rated by at least {min_group} members.")


# ── Footer ───────────────────────────────────────────────────────────────────

st.divider()
st.markdown(
    "*Talent-Augmenting OS: Making workers better, not dependent. "
    "Aggregate-only by design.*"
)
