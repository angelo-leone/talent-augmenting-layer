"""
Profile Manager — CRUD operations for Talent-Augmenting Layer profiles.

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
        """Classify a task using stem-level keyword overlap against profile categories.

        - Strips explanatory text (after em-dash, parenthetical) from task items.
        - Reduces words to a 4-char stem so "writing" matches "write",
          "arguing" matches "argumentation", etc.
        - Priority: protect and hands_off outrank equal scores in other
          categories. Red lines are not used to override classification
          (many red lines are "do it but coach-mode", not "never do it");
          the caller is expected to surface the relevant red line as
          advisory copy alongside the mode.
        """
        STOPWORDS = {
            "", "a", "the", "an", "to", "for", "of", "and", "in", "my", "me",
            "some", "this", "these", "with", "on", "by", "be", "is", "are",
            "that", "it", "as", "at", "from", "or",
        }

        def _stem(word: str) -> str:
            """Reduce to a 4-char prefix after stripping obvious English
            suffixes. Conflates "write" / "writing" / "writer" to "writ",
            "format" / "formatting" / "formatted" to "form", etc. Some
            false positives (e.g. "word"/"work") are tolerable at the 0.3
            match threshold."""
            if len(word) < 5:
                return word
            for suf in ("ations", "ation", "ings", "ing", "ers", "er",
                        "ions", "ion", "ly", "es", "ed", "s"):
                if word.endswith(suf) and len(word) > len(suf) + 3:
                    word = word[: -len(suf)]
                    break
            return word[:4] if len(word) >= 4 else word

        def _tokenise(text: str) -> set[str]:
            words = (w for w in re.split(r"\W+", text.lower()) if w)
            return {_stem(w) for w in words if w not in STOPWORDS}

        def _clean_task(task: str) -> str:
            task = re.split(r"\s*[—–]\s*", task)[0]
            task = re.sub(r"\(.*?\)", "", task)
            return task.strip()

        desc_tokens = _tokenise(task_description)
        desc_lower = task_description.lower()

        def _score(task_list: list[str]) -> float:
            best = 0.0
            for task in task_list:
                cleaned = _clean_task(task)
                task_tokens = _tokenise(cleaned)
                if not task_tokens:
                    continue
                overlap = len(desc_tokens & task_tokens)
                score = overlap / len(task_tokens) if task_tokens else 0.0
                # Substring boost: any task stem that appears inside the raw
                # description still counts, to catch cases the tokeniser missed.
                for tt in task_tokens:
                    if len(tt) >= 4 and tt in desc_lower:
                        score = max(score, 0.4)
                best = max(best, score)
            return best

        candidates = [
            ("protect", _score(self.tasks.protect)),
            ("hands_off", _score(self.tasks.hands_off)),
            ("coach", _score(self.tasks.coach)),
            ("automate", _score(self.tasks.automate)),
            ("augment", _score(self.tasks.augment)),
        ]

        # Safety bias: when scoring is close, prefer protect / hands_off.
        # Under-classifying protect is worse than over-classifying (a user
        # can say /talent-speed to bypass friction, but skill atrophy from
        # missed protect classifications is silent and cumulative).
        PROTECT_BIAS = 0.1
        adjusted = [
            (cat, score + (PROTECT_BIAS if cat in ("protect", "hands_off") else 0.0))
            for cat, score in candidates
        ]
        best_cat, _ = max(adjusted, key=lambda pair: pair[1])
        original_best = dict(candidates)[best_cat]

        if original_best < 0.3:
            # Nothing in the profile matches. Returning "unknown" lets the
            # caller ask the user how to handle it (automate now vs. coach
            # long-term) and add the new domain/task to the profile, rather
            # than silently falling back to augment.
            return "unknown"
        return best_cat


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

        Best-effort parser. Profiles are primarily human-readable markdown
        so small formatting drifts are expected, but the fields below are
        required by talent_status / classify_task / the admin dashboard
        and have to come out correctly for a well-formed profile.
        """
        profile = Profile(name=name)

        # ── Section 1: Identity Card ─────────────────────────────────
        identity = self._extract_section(content, r"##\s+1\.?\s+Identity Card")
        if identity:
            for field_name, attr in [
                ("Name", "name"),
                ("Role", "role"),
                ("Organisation", "organization"),
                ("Organization", "organization"),
                ("Industry", "industry"),
            ]:
                m = re.search(
                    rf"\|\s*\*\*{field_name}\*\*\s*\|\s*(.+?)\s*\|",
                    identity,
                    re.IGNORECASE,
                )
                if m:
                    val = m.group(1).strip()
                    if attr == "name" and val:
                        profile.name = val
                    elif val:
                        setattr(profile, attr, val)
            ctx = re.search(
                r"\*\*Context summary\*\*:\s*(.+?)(?:\n\n|\Z)",
                identity,
                re.DOTALL,
            )
            if ctx:
                profile.context_summary = ctx.group(1).strip()

        # ── Section 2: Expertise Map (scoped, so contrast tables don't leak) ──
        expertise_section = self._extract_section(content, r"##\s+2\.?\s+Expertise Map")
        if expertise_section:
            expertise_pattern = r"\|\s*([^|\n]+?)\s*\|\s*(\d)\s*[^|]*?\|\s*([^|\n]*?)\s*\|\s*([^|\n]*?)\s*\|"
            for match in re.finditer(expertise_pattern, expertise_section):
                domain = match.group(1).strip()
                # Filter out header rows, divider rows, and obvious garbage.
                if not domain or domain.lower() == "domain":
                    continue
                if set(domain) <= {"-"} or "---" in domain:
                    continue
                if domain.startswith("**") and domain.endswith("**"):
                    continue
                try:
                    rating = int(match.group(2))
                except ValueError:
                    continue
                profile.expertise.append(ExpertiseRating(
                    domain=domain,
                    rating=rating,
                    evidence=match.group(3).strip(),
                    growth_direction=match.group(4).strip(),
                ))

        # ── Section 3: AI Relationship Status (dependency risk) ──────
        ai_section = self._extract_section(content, r"##\s+3\.?\s+AI Relationship")
        if ai_section:
            m = re.search(r"Dependency Risk Score\*?\*?:?\s*(\d+)\s*/\s*10", ai_section)
            if m:
                profile.dependency_risk_score = int(m.group(1))

        # ── Section 4: Growth Trajectory ─────────────────────────────
        growth_section = self._extract_section(content, r"##\s+4\.?\s+Growth Trajectory")
        if growth_section:
            gp = re.search(r"Growth Potential Score\*?\*?:?\s*(\d+)\s*/\s*10", growth_section)
            if gp:
                profile.growth_potential_score = int(gp.group(1))
            for list_name, attr in [
                ("Skills to develop", "skills_to_develop"),
                ("Skills to protect", "skills_to_protect"),
                ("Career goals", "career_goals"),
            ]:
                items = self._extract_subsection_list(growth_section, list_name)
                if items:
                    setattr(profile, attr, items)

        # ── Section 7: Calibration YAML ──────────────────────────────
        yaml_match = re.search(r"```yaml\n(.*?)```", content, re.DOTALL)
        if yaml_match:
            self._parse_calibration_yaml(yaml_match.group(1), profile.calibration)

        # ── Section 6: Task Classifications ──────────────────────────
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

        # ── Section 8: Red Lines ─────────────────────────────────────
        red_lines_section = re.search(
            r"## 8\.?\s+Red Lines.*?\n(.*?)(?=\n##\s|\Z)",
            content, re.DOTALL
        )
        if red_lines_section:
            for line in red_lines_section.group(1).split("\n"):
                cleaned = re.sub(r"^\d+\.\s*\*\*", "", line.strip())
                cleaned = cleaned.replace("**", "").strip()
                if not cleaned:
                    continue
                # Skip markdown dividers and other non-red-line chrome.
                if set(cleaned) <= {"-"} or cleaned.startswith("Things this"):
                    continue
                profile.red_lines.append(cleaned)

        return profile

    @staticmethod
    def _extract_section(content: str, header_re: str) -> str:
        """Return the body of a top-level `## N.` section, or empty string."""
        m = re.search(
            rf"{header_re}[^\n]*\n(.*?)(?=\n##\s|\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        return m.group(1) if m else ""

    @staticmethod
    def _extract_subsection_list(section: str, label: str) -> list[str]:
        """Extract a numbered or bulleted list under `**Label**:` within a section."""
        m = re.search(
            rf"\*\*{re.escape(label)}\*\*:?\s*\n(.*?)(?=\n\n|\n\*\*|\n##|\Z)",
            section,
            re.DOTALL | re.IGNORECASE,
        )
        if not m:
            return []
        items: list[str] = []
        for line in m.group(1).split("\n"):
            line = line.strip()
            # Strip list marker (-, *, 1., 2., etc.)
            stripped = re.sub(r"^(?:[-*]|\d+\.)\s+", "", line)
            if stripped and stripped != line:
                # Only count lines that had a list marker
                items.append(stripped)
        return items

    @staticmethod
    def _parse_calibration_yaml(yaml_text: str, calibration: CalibrationSettings) -> None:
        """Tiny YAML-ish parser for the calibration block.

        Handles scalar keys and simple `- item` lists. Does not cover the
        full YAML spec; the calibration block is written by TAL and stays
        within this subset.
        """
        current_list_key: str | None = None
        list_keys = {
            "cognitive_forcing_domains",
            "contrastive_explanation_domains",
            "automation_permissions",
        }
        for raw_line in yaml_text.splitlines():
            line = raw_line.rstrip()
            if not line.strip():
                continue
            if line.lstrip().startswith("#"):
                continue
            if line.startswith(" ") or line.startswith("\t"):
                item = line.strip()
                if item.startswith("- ") and current_list_key:
                    value = item[2:].strip()
                    if current_list_key == "cognitive_forcing_domains":
                        calibration.cognitive_forcing_domains.append(value)
                    elif current_list_key == "contrastive_explanation_domains":
                        calibration.contrastive_explanation_domains.append(value)
                    elif current_list_key == "automation_permissions":
                        calibration.automation_permissions.append(value)
                continue
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.split("#", 1)[0].strip()  # strip inline comments
            current_list_key = key if key in list_keys and not val else None
            if current_list_key:
                continue
            if key == "default_friction_level":
                calibration.default_friction_level = val
            elif key == "coaching_frequency":
                calibration.coaching_frequency = val
            elif key == "challenge_level":
                calibration.challenge_level = val
            elif key == "feedback_style":
                calibration.feedback_style = val
            elif key == "explanation_depth":
                calibration.explanation_depth = val

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
        """Aggregate anonymized stats across ALL profiles for org-level dashboard."""
        profiles_data = []
        for name in self.list_profiles():
            profile = self.read_profile(name)
            if not profile:
                continue

            expertise_ratings = [e.rating for e in profile.expertise]
            avg_expertise = sum(expertise_ratings) / len(expertise_ratings) if expertise_ratings else 0

            progression = self.get_skill_progression(name)

            profiles_data.append({
                "name": name,
                "role": profile.role,
                "expertise_avg": round(avg_expertise, 1),
                "expertise_count": len(expertise_ratings),
                "expertise_by_domain": {e.domain: e.rating for e in profile.expertise},
                "dependency_risk": profile.dependency_risk_score,
                "growth_potential": profile.growth_potential_score,
                "friction_level": profile.calibration.default_friction_level,
                "total_interactions": progression.get("total_interactions", 0),
                "passive_ratio": progression.get("passive_ratio", 0),
                "atrophy_warnings": progression.get("atrophy_warnings", []),
                "trend_direction": progression.get("trend_direction", "no_data"),
            })

        if not profiles_data:
            return {"message": "No profiles found.", "profiles": []}

        # Org-level aggregations
        total_profiles = len(profiles_data)
        avg_dependency = sum(p["dependency_risk"] for p in profiles_data) / total_profiles
        avg_growth = sum(p["growth_potential"] for p in profiles_data) / total_profiles
        avg_expertise = sum(p["expertise_avg"] for p in profiles_data) / total_profiles
        declining_count = sum(1 for p in profiles_data if p["trend_direction"] == "declining")
        at_risk_count = sum(1 for p in profiles_data if p["dependency_risk"] >= 7)

        # Domain-level aggregation
        all_domains: dict[str, list[int]] = {}
        for p in profiles_data:
            for domain, rating in p["expertise_by_domain"].items():
                if domain not in all_domains:
                    all_domains[domain] = []
                all_domains[domain].append(rating)

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
            "total_profiles": total_profiles,
            "org_averages": {
                "dependency_risk": round(avg_dependency, 1),
                "growth_potential": round(avg_growth, 1),
                "expertise": round(avg_expertise, 1),
            },
            "alerts": {
                "at_risk_count": at_risk_count,
                "declining_trend_count": declining_count,
                "total_atrophy_warnings": sum(len(p["atrophy_warnings"]) for p in profiles_data),
            },
            "domain_summary": domain_summary,
            "profiles": profiles_data,
        }
