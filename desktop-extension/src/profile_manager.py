"""
Profile Manager: CRUD operations for Talent-Augmenting OS profiles.

Handles reading, writing, searching, and updating user profiles.
Profiles are stored as markdown files in a configurable directory.
"""

from __future__ import annotations

import os
import re
import json
import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


def parse_tal_log(text: str) -> list[dict]:
    """Extract ``<tal_log>`` JSON blocks from LLM response text.

    Returns a list of dicts with keys matching the telemetry schema:
    task_category, domain, engagement_level, skill_signal, notes.
    Silently skips malformed blocks.
    """
    results: list[dict] = []
    TAG_OPEN = "<tal_log>"
    TAG_CLOSE = "</tal_log>"
    start = 0
    while True:
        idx = text.find(TAG_OPEN, start)
        if idx == -1:
            break
        end = text.find(TAG_CLOSE, idx + len(TAG_OPEN))
        if end == -1:
            break
        payload = text[idx + len(TAG_OPEN):end].strip()
        try:
            data = json.loads(payload)
            if isinstance(data, dict):
                results.append({
                    "task_category": str(data.get("task_category", "augment")),
                    "domain": str(data.get("domain", "")),
                    "engagement_level": str(data.get("engagement_level", "active")),
                    "skill_signal": str(data.get("skill_signal", "none")),
                    "notes": str(data.get("notes", "")),
                })
        except (json.JSONDecodeError, TypeError):
            pass
        start = end + len(TAG_CLOSE)
    return results


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class ExpertiseRating:
    domain: str
    rating: int  # 1-5
    evidence: str = ""
    growth_direction: str = ""

    def label(self) -> str:
        labels = {1: "Novice", 2: "Developing", 3: "Proficient", 4: "Advanced", 5: "Expert"}
        return labels.get(self.rating, "Unknown")


@dataclass
class TaskClassification:
    automate: list[str] = field(default_factory=list)
    augment: list[str] = field(default_factory=list)
    coach: list[str] = field(default_factory=list)
    protect: list[str] = field(default_factory=list)
    hands_off: list[str] = field(default_factory=list)


@dataclass
class CalibrationSettings:
    default_friction_level: str = "medium"  # low, medium, high
    cognitive_forcing_domains: list[str] = field(default_factory=list)
    contrastive_explanation_domains: list[str] = field(default_factory=list)
    automation_permissions: list[str] = field(default_factory=list)
    coaching_frequency: str = "medium"  # low, medium, high
    challenge_level: str = "medium"  # low, medium, high
    feedback_style: str = "balanced"  # socratic, direct, examples, balanced
    explanation_depth: str = "frameworks"  # minimal, rationale, frameworks, full


@dataclass
class InteractionLog:
    timestamp: str
    task_category: str  # automate, augment, coach, protect, hands_off
    domain: str
    engagement_level: str  # passive, active, critical
    skill_signal: str  # growth, stable, atrophy, none
    notes: str = ""


@dataclass
class Profile:
    name: str
    role: str = ""
    organization: str = ""
    industry: str = ""
    context_summary: str = ""
    expertise: list[ExpertiseRating] = field(default_factory=list)
    ai_tools: list[str] = field(default_factory=list)
    ai_frequency: str = ""
    ai_interaction_pattern: str = ""
    dependency_risk_score: int = 0
    growth_potential_score: int = 0
    career_goals: list[str] = field(default_factory=list)
    skills_to_develop: list[str] = field(default_factory=list)
    skills_to_protect: list[str] = field(default_factory=list)
    tasks: TaskClassification = field(default_factory=TaskClassification)
    calibration: CalibrationSettings = field(default_factory=CalibrationSettings)
    red_lines: list[str] = field(default_factory=list)
    interaction_log: list[InteractionLog] = field(default_factory=list)
    learning_style: str = ""
    feedback_style: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def get_domain_rating(self, domain: str) -> Optional[ExpertiseRating]:
        for exp in self.expertise:
            if exp.domain.lower() == domain.lower():
                return exp
        return None

    def get_friction_level(self, domain: str) -> str:
        rating = self.get_domain_rating(domain)
        if not rating:
            return self.calibration.default_friction_level

        if domain.lower() in [d.lower() for d in self.calibration.cognitive_forcing_domains]:
            return "high"
        if domain.lower() in [d.lower() for d in self.calibration.automation_permissions]:
            return "low"
        if rating.rating <= 2:
            return "high"
        if rating.rating == 3:
            return "medium"
        return "low"

    def classify_task(self, task_description: str) -> str:
        """Classify a task using keyword overlap scoring against profile categories.

        Strips explanatory text (after:, dashes, parenthetical notes) from task
        list items before matching. Uses word-level overlap scoring. Priority
        order: protect > hands_off > coach > automate > augment.
        """
        desc_lower = task_description.lower()
        desc_words = set(re.split(r"\W+", desc_lower)) - {"", "a", "the", "an", "to", "for", "of", "and", "in", "my", "me", "some", "this", "these", "with", "on"}

        def _clean_task(task: str) -> str:
            """Strip explanatory text from task items."""
            # Remove everything after em-dash, regular dash phrase, or parenthetical
            task = re.split(r"\s*[, –]\s*", task)[0]
            task = re.sub(r"\(.*?\)", "", task)
            return task.strip()

        def _score(task_list: list[str]) -> float:
            best = 0.0
            for task in task_list:
                cleaned = _clean_task(task)
                task_words = set(re.split(r"\W+", cleaned.lower())) - {"", "a", "the", "an", "to", "for", "of", "and", "in"}
                if not task_words:
                    continue
                overlap = len(desc_words & task_words)
                # Score: proportion of task keywords found in description
                score = overlap / len(task_words) if task_words else 0
                # Also check if any task keyword appears as substring in description
                for tw in task_words:
                    if len(tw) > 3 and tw in desc_lower:
                        score = max(score, 0.4)
                best = max(best, score)
            return best

        # Priority order matters: protect and hands_off checked first
        categories = [
            ("protect", self.tasks.protect),
            ("hands_off", self.tasks.hands_off),
            ("coach", self.tasks.coach),
            ("automate", self.tasks.automate),
            ("augment", self.tasks.augment),
        ]

        best_cat = "augment"
        best_score = 0.0
        for cat_name, cat_tasks in categories:
            s = _score(cat_tasks)
            if s > best_score:
                best_score = s
                best_cat = cat_name

        return best_cat if best_score >= 0.3 else "augment"


# ── Profile Storage ──────────────────────────────────────────────────────────

class ProfileStore:
    """Manages profile persistence as markdown files."""

    def __init__(self, profiles_dir: str | Path):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def _profile_path(self, name: str) -> Path:
        safe_name = re.sub(r"[^a-z0-9]", "-", name.lower()).strip("-")
        return self.profiles_dir / f"tal-{safe_name}.md"

    def _legacy_profile_path(self, name: str) -> Path:
        safe_name = re.sub(r"[^a-z0-9]", "-", name.lower()).strip("-")
        return self.profiles_dir / f"pro-{safe_name}.md"

    def _resolve_existing_profile_path(self, name: str) -> Path | None:
        """Return existing tal- or legacy pro- profile path for a user."""
        tal_path = self._profile_path(name)
        if tal_path.exists():
            return tal_path
        legacy_path = self._legacy_profile_path(name)
        if legacy_path.exists():
            return legacy_path
        return None

    def list_profiles(self) -> list[str]:
        """Return names of all existing profiles."""
        names: set[str] = set()
        for pattern in ("tal-*.md", "pro-*.md"):
            for f in self.profiles_dir.glob(pattern):
                stem = f.stem
                if stem.startswith("tal-"):
                    raw_name = stem.replace("tal-", "", 1)
                else:
                    raw_name = stem.replace("pro-", "", 1)
                names.add(raw_name.replace("-", " ").title())
        return sorted(names)

    def profile_exists(self, name: str) -> bool:
        return self._resolve_existing_profile_path(name) is not None

    def read_profile_raw(self, name: str) -> str | None:
        path = self._resolve_existing_profile_path(name)
        if path is None:
            return None
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def write_profile_raw(self, name: str, content: str) -> Path:
        path = self._profile_path(name)
        path.write_text(content, encoding="utf-8")
        return path

    def read_profile(self, name: str) -> Profile | None:
        """Read and parse a profile from markdown. Returns structured Profile."""
        raw = self.read_profile_raw(name)
        if not raw:
            return None
        return self._parse_profile(name, raw)

    def _parse_profile(self, name: str, content: str) -> Profile:
        """Parse markdown profile into structured Profile object.

        This is a best-effort parser: profiles are primarily
        human-readable markdown and may not parse perfectly.
        """
        profile = Profile(name=name)

        # Extract expertise ratings from tables
        expertise_pattern = r"\|\s*(.+?)\s*\|\s*(\d)\s*.*?\|\s*(.*?)\s*\|\s*(.*?)\s*\|"
        for match in re.finditer(expertise_pattern, content):
            domain = match.group(1).strip()
            if domain and domain != "Domain" and not domain.startswith("--"):
                try:
                    rating = int(match.group(2))
                    profile.expertise.append(ExpertiseRating(
                        domain=domain,
                        rating=rating,
                        evidence=match.group(3).strip(),
                        growth_direction=match.group(4).strip()
                    ))
                except ValueError:
                    pass

        # Extract calibration from yaml block
        yaml_match = re.search(r"```yaml\n(.*?)```", content, re.DOTALL)
        if yaml_match:
            yaml_text = yaml_match.group(1)
            for line in yaml_text.strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    if key == "default_friction_level":
                        profile.calibration.default_friction_level = val
                    elif key == "coaching_frequency":
                        profile.calibration.coaching_frequency = val
                    elif key == "challenge_level":
                        profile.calibration.challenge_level = val
                    elif key == "feedback_style":
                        profile.calibration.feedback_style = val
                    elif key == "explanation_depth":
                        profile.calibration.explanation_depth = val

        # Extract task classifications
        task_sections = {
            "### Automate": "automate",
            "### Augment": "augment",
            "### Coach": "coach",
            "### Protect": "protect",
            "### Hands-off": "hands_off",
        }
        for header, attr in task_sections.items():
            pattern = re.escape(header) + r".*?\n(.*?)(?=\n###|\n## |\Z)"
            section = re.search(pattern, content, re.DOTALL)
            if section:
                items = []
                for line in section.group(1).split("\n"):
                    line = line.strip()
                    if line.startswith("- "):
                        items.append(line[2:].strip())
                setattr(profile.tasks, attr, items)

        # Extract red lines
        red_lines_section = re.search(
            r"## 8\. Red Lines.*?\n(.*?)(?=\n## |\Z)",
            content, re.DOTALL
        )
        if red_lines_section:
            for line in red_lines_section.group(1).split("\n"):
                cleaned = re.sub(r"^\d+\.\s*\*\*", "", line.strip())
                cleaned = cleaned.replace("**", "").strip()
                if cleaned and not cleaned.startswith("Things this"):
                    profile.red_lines.append(cleaned)

        return profile

    def log_interaction(self, name: str, log: InteractionLog) -> None:
        """Append an interaction log entry to the profile."""
        profile = self.read_profile(name)
        if not profile:
            return
        profile.interaction_log.append(log)
        # Append to the interaction log file
        log_path = self.profiles_dir / f"log-{re.sub(r'[^a-z0-9]', '-', name.lower())}.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(log)) + "\n")

    def read_interaction_log(self, name: str) -> list[InteractionLog]:
        """Read all interaction logs for a user."""
        safe_name = re.sub(r"[^a-z0-9]", "-", name.lower()).strip("-")
        log_path = self.profiles_dir / f"log-{safe_name}.jsonl"
        if not log_path.exists():
            return []
        logs = []
        for line in log_path.read_text(encoding="utf-8").strip().split("\n"):
            if line.strip():
                data = json.loads(line)
                logs.append(InteractionLog(**data))
        return logs

    def get_skill_progression(self, name: str) -> dict:
        """Analyze interaction logs to show skill progression."""
        logs = self.read_interaction_log(name)
        if not logs:
            return {"message": "No interaction logs yet. Use the system and run /talent-update to start tracking."}

        # Count by domain and signal
        domain_signals: dict[str, dict[str, int]] = {}
        category_counts: dict[str, int] = {}
        engagement_counts: dict[str, int] = {}

        for log in logs:
            # Domain signals
            if log.domain not in domain_signals:
                domain_signals[log.domain] = {"growth": 0, "stable": 0, "atrophy": 0}
            if log.skill_signal in domain_signals[log.domain]:
                domain_signals[log.domain][log.skill_signal] += 1

            # Category distribution
            category_counts[log.task_category] = category_counts.get(log.task_category, 0) + 1

            # Engagement levels
            engagement_counts[log.engagement_level] = engagement_counts.get(log.engagement_level, 0) + 1

        total = len(logs)

        # Time-series trend analysis: split into weekly buckets
        weekly_trends: dict[str, dict[str, int]] = {}
        for log in logs:
            try:
                dt = datetime.datetime.fromisoformat(log.timestamp)
                week_key = dt.strftime("%Y-W%W")
            except (ValueError, TypeError):
                week_key = "unknown"
            if week_key not in weekly_trends:
                weekly_trends[week_key] = {"total": 0, "passive": 0, "growth": 0, "atrophy": 0}
            weekly_trends[week_key]["total"] += 1
            if log.engagement_level == "passive":
                weekly_trends[week_key]["passive"] += 1
            if log.skill_signal == "growth":
                weekly_trends[week_key]["growth"] += 1
            elif log.skill_signal == "atrophy":
                weekly_trends[week_key]["atrophy"] += 1

        # Compute engagement trend direction
        weeks_sorted = sorted(weekly_trends.keys())
        trend_direction = "stable"
        if len(weeks_sorted) >= 2:
            recent = weekly_trends[weeks_sorted[-1]]
            prev = weekly_trends[weeks_sorted[-2]]
            recent_passive = recent["passive"] / max(recent["total"], 1)
            prev_passive = prev["passive"] / max(prev["total"], 1)
            if recent_passive > prev_passive + 0.15:
                trend_direction = "declining"
            elif recent_passive < prev_passive - 0.15:
                trend_direction = "improving"

        return {
            "total_interactions": total,
            "domain_signals": domain_signals,
            "task_distribution": category_counts,
            "engagement_distribution": engagement_counts,
            "passive_ratio": engagement_counts.get("passive", 0) / total if total > 0 else 0,
            "atrophy_warnings": [
                domain for domain, signals in domain_signals.items()
                if signals.get("atrophy", 0) > signals.get("growth", 0)
            ],
            "weekly_trends": weekly_trends,
            "trend_direction": trend_direction,
        }

    def delete_profile(self, name: str) -> bool:
        """Delete a profile and its interaction log."""
        path = self._resolve_existing_profile_path(name)
        safe_name = re.sub(r"[^a-z0-9]", "-", name.lower()).strip("-")
        log_path = self.profiles_dir / f"log-{safe_name}.jsonl"
        deleted = False
        if path and path.exists():
            path.unlink()
            deleted = True
        if log_path.exists():
            log_path.unlink()
        return deleted

    def get_org_summary(self) -> dict:
        """Aggregate-only org view. No individual is ever exposed.

        Mirrors hosted/org_service.py. Per-profile metrics are computed only to
        build org-level aggregates and are never returned; aggregates are
        suppressed below k-anonymity floors so no individual can be singled out
        in a small team. Individual data stays visible only to the member.
        """
        # k-anonymity floors (keep in sync with hosted/org_service.py).
        MIN_AGGREGATE_GROUP = 5   # min profiles before any aggregate is shown
        MIN_SENSITIVE_GROUP = 10  # min profiles before risk/atrophy alerts show

        dep_risks: list[float] = []
        growth_potentials: list[float] = []
        expertise_avgs: list[float] = []
        all_domains: dict[str, list[int]] = {}
        risk_buckets = {"low": 0, "medium": 0, "high": 0, "none": 0}
        at_risk_count = 0
        declining_count = 0
        atrophy_members = 0
        # Identity/role only, for administration. No skill/risk/behaviour data.
        members_admin: list[dict] = []

        for name in self.list_profiles():
            profile = self.read_profile(name)
            if not profile:
                continue

            members_admin.append({"name": name, "role": profile.role})

            expertise_ratings = [e.rating for e in profile.expertise]
            if expertise_ratings:
                expertise_avgs.append(sum(expertise_ratings) / len(expertise_ratings))
            for e in profile.expertise:
                all_domains.setdefault(e.domain, []).append(e.rating)

            progression = self.get_skill_progression(name)
            dep = profile.dependency_risk_score
            dep_risks.append(dep)
            growth_potentials.append(profile.growth_potential_score)

            if dep >= 7:
                risk_buckets["high"] += 1
                at_risk_count += 1
            elif dep >= 4:
                risk_buckets["medium"] += 1
            else:
                risk_buckets["low"] += 1

            if progression.get("trend_direction") == "declining":
                declining_count += 1
            if len(progression.get("atrophy_warnings", [])) >= 3:
                atrophy_members += 1

        total_profiles = len(members_admin)
        if total_profiles == 0:
            return {"message": "No profiles found.", "members": []}

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

        # Only domains rated by >= MIN_AGGREGATE_GROUP members; avg + count only
        # (min/max would expose the extreme individual).
        domain_summary = {
            domain: {"avg": round(sum(ratings) / len(ratings), 1), "count": len(ratings)}
            for domain, ratings in all_domains.items()
            if len(ratings) >= MIN_AGGREGATE_GROUP
        }

        alerts = None
        if sensitive_ok:
            alerts = {
                "at_risk_count": at_risk_count,
                "declining_trend_count": declining_count,
                "atrophy_signal_members": atrophy_members,
            }

        return {
            "total_profiles": total_profiles,
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
