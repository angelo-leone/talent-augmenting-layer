"""
Profile Manager — CRUD operations for Pro Worker AI profiles.

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

        Strips explanatory text (after —, dashes, parenthetical notes) from task
        list items before matching. Uses word-level overlap scoring. Priority
        order: protect > hands_off > coach > automate > augment.
        """
        desc_lower = task_description.lower()
        desc_words = set(re.split(r"\W+", desc_lower)) - {"", "a", "the", "an", "to", "for", "of", "and", "in", "my", "me", "some", "this", "these", "with", "on"}

        def _clean_task(task: str) -> str:
            """Strip explanatory text from task items."""
            # Remove everything after em-dash, regular dash phrase, or parenthetical
            task = re.split(r"\s*[—–]\s*", task)[0]
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

        # Priority order matters — protect and hands_off checked first
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
        return self.profiles_dir / f"pro-{safe_name}.md"

    def list_profiles(self) -> list[str]:
        """Return names of all existing profiles."""
        profiles = []
        for f in self.profiles_dir.glob("pro-*.md"):
            name = f.stem.replace("pro-", "").replace("-", " ").title()
            profiles.append(name)
        return profiles

    def profile_exists(self, name: str) -> bool:
        return self._profile_path(name).exists()

    def read_profile_raw(self, name: str) -> str | None:
        path = self._profile_path(name)
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

        This is a best-effort parser — profiles are primarily
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
            return {"message": "No interaction logs yet. Use the system and run /proworker-update to start tracking."}

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
        }
