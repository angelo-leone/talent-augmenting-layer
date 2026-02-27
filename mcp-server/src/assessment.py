"""
Pro Worker AI — Embedded Assessment Engine

The full PWAQ (Pro Worker Assessment Questionnaire) embedded in the MCP server.
Any chatbot connected via MCP can drive the onboarding assessment conversationally,
compute scores, and auto-create/update the user's profile.

Architecture:
  - Question bank: All PWAQ items with behavioral anchors (stateless)
  - Score computation: Server-side math from raw answers (stateless)
  - Profile generation: Creates a full profile markdown from scores + demographics
  - The LLM drives the conversation; the MCP does the math and storage
"""

from __future__ import annotations

import datetime
import math
from dataclasses import dataclass, field, asdict
from typing import Any


# ── Question Bank ────────────────────────────────────────────────────────────

SECTION_A_QUESTIONS = [
    {
        "id": "A1",
        "title": "Output Acceptance Pattern",
        "question": "When AI generates a response for a work task, what do you typically do?",
        "anchors": {
            1: "I use AI output purely as a thinking prompt — I always write my own version",
            2: "I substantially rewrite AI output, keeping maybe 20-30% of the original",
            3: "I edit AI output moderately — restructuring sections and rewriting key parts",
            4: "I lightly edit AI output for tone and accuracy, keeping most of the structure",
            5: "I use AI output as-is or with minimal changes most of the time",
        },
    },
    {
        "id": "A2",
        "title": "Skill Atrophy Awareness",
        "question": "Thinking about skills you use AI for regularly, how would you rate your independent ability compared to before you started using AI?",
        "reverse_coded": True,
        "anchors": {
            1: "My independent skills have improved — AI helps me learn and practice",
            2: "My skills are about the same — AI supplements but hasn't changed my ability",
            3: "I'm not sure — I haven't tested my independent ability recently",
            4: "Some skills feel weaker — I'd struggle more without AI than I used to",
            5: "I've lost significant ability — I depend on AI for things I could do alone before",
        },
    },
    {
        "id": "A3",
        "title": "Critical Evaluation Depth",
        "question": "When AI gives you an answer that looks reasonable, what is your typical response?",
        "anchors": {
            1: "I systematically verify claims, check sources, and stress-test the reasoning",
            2: "I check key facts and challenge the main argument before accepting",
            3: "I scan for obvious errors but generally trust the reasoning if it looks right",
            4: "I occasionally spot-check but usually move on if the output seems decent",
            5: "I rarely question AI output — if it looks professional, I accept it",
        },
    },
    {
        "id": "A4",
        "title": "Task Delegation Breadth",
        "question": "What proportion of your complex cognitive work (strategy, analysis, writing, decision-making) do you delegate to AI?",
        "anchors": {
            1: "Less than 10% — I use AI mainly for mechanical tasks",
            2: "About 20-30% — AI assists on specific subtasks within complex work",
            3: "About 40-50% — AI does first drafts and I refine",
            4: "About 60-70% — AI handles most of the heavy lifting, I direct and review",
            5: "Over 80% — AI generates most of my complex work products",
        },
    },
    {
        "id": "A5",
        "title": "AI-Free Capability",
        "question": "If AI tools were unavailable for a week, how would your work quality and output be affected?",
        "reverse_coded": True,
        "anchors": {
            1: "Minimal impact — I'd be slower but the quality would be the same",
            2: "Moderate slowdown but I could maintain quality on important tasks",
            3: "Significant impact — several tasks would suffer noticeably",
            4: "Severe impact — I'd struggle to deliver key work products at current quality",
            5: "I couldn't function effectively — AI is essential to my core work",
        },
    },
]

SECTION_B_QUESTIONS = [
    {
        "id": "B1",
        "title": "Goal Clarity",
        "question": "How clearly can you describe what professional growth looks like for you in the next 1-2 years?",
        "anchors": {
            1: "I haven't thought about it — I'm focused on day-to-day tasks",
            2: "I have a vague sense of direction but no specific goals",
            3: "I have broad goals but not specific plans",
            4: "I have clear goals with some specific skills and milestones identified",
            5: "I have a detailed development plan with specific skills, timelines, and measures",
        },
    },
    {
        "id": "B2",
        "title": "Feedback Orientation",
        "question": "When someone (or AI) challenges your work or suggests a different approach, how do you typically respond?",
        "anchors": {
            1: "I find it uncomfortable and tend to defend my original approach",
            2: "I listen but often feel defensive initially",
            3: "I'm open to feedback when it's delivered constructively",
            4: "I actively seek feedback and find challenges energizing",
            5: "I deliberately seek out disagreement and use it to sharpen my thinking",
        },
    },
    {
        "id": "B3",
        "title": "Deliberate Practice",
        "question": "In the past month, how often have you deliberately practiced a skill you're developing (not just doing your job, but intentionally working on getting better)?",
        "anchors": {
            1: "Never — I learn on the job but don't practice deliberately",
            2: "Once — I did one specific learning activity",
            3: "A few times — I've sought out opportunities to practice",
            4: "Weekly — I regularly carve out time for skill development",
            5: "Multiple times per week — I have a structured practice routine",
        },
    },
    {
        "id": "B4",
        "title": "Learning Transfer",
        "question": "When you learn something new (from AI, a course, a colleague), how do you apply it?",
        "anchors": {
            1: "I rarely apply new learning — it stays theoretical",
            2: "I occasionally apply things when the situation is obvious",
            3: "I try to apply new concepts but don't always succeed",
            4: "I actively look for opportunities to apply new learning in my work",
            5: "I create systems to apply and reinforce new learning (notes, checklists, frameworks)",
        },
    },
    {
        "id": "B5",
        "title": "Metacognitive Awareness",
        "question": "How well can you identify what you're good at, what you're bad at, and what you need to learn?",
        "anchors": {
            1: "I find it hard to self-assess accurately — I'm often surprised by feedback",
            2: "I have a general sense but am often wrong about specific skills",
            3: "I can identify broad strengths and weaknesses but not always the details",
            4: "I have a clear picture of my skill levels and can articulate gaps",
            5: "I regularly calibrate my self-assessment against external evidence and adjust",
        },
    },
]

SECTION_D_QUESTIONS = [
    {
        "id": "D1",
        "title": "Capability Calibration",
        "question": "How well do you predict what AI can and cannot do before trying?",
        "anchors": {
            1: "I'm often surprised — both positively and negatively — by AI output",
            2: "I sometimes misjudge — I over- or under-estimate AI ability",
            3: "I'm usually right about whether AI will handle a task well",
            4: "I have a nuanced sense of AI strengths and weaknesses by task type",
            5: "I can predict AI output quality with high accuracy and know exactly how to work around limitations",
        },
    },
    {
        "id": "D2",
        "title": "Prompt Effectiveness",
        "question": "How effective are you at getting AI to produce useful output?",
        "anchors": {
            1: "I write simple prompts and take whatever comes back",
            2: "I iterate a few times if the first output isn't right",
            3: "I provide context and constraints to get better output",
            4: "I systematically structure prompts with role, context, constraints, and examples",
            5: "I use advanced techniques (chain-of-thought, few-shot, tools) and consistently get excellent results",
        },
    },
    {
        "id": "D3",
        "title": "Error Detection",
        "question": "How often do you catch errors, hallucinations, or subtle mistakes in AI output?",
        "anchors": {
            1: "Rarely — I usually trust what the AI says",
            2: "Occasionally — I catch obvious errors but miss subtle ones",
            3: "Often — I check key facts and catch most substantive errors",
            4: "Almost always — I have a systematic approach to verifying AI output",
            5: "Always — I treat every AI output as draft and verify independently",
        },
    },
    {
        "id": "D4",
        "title": "Appropriate Delegation",
        "question": "How well do you match tasks to the right level of AI involvement?",
        "anchors": {
            1: "I use AI for everything or nothing — no differentiation by task type",
            2: "I use AI for obvious tasks (search, formatting) but not strategically",
            3: "I think about which tasks benefit from AI and which don't",
            4: "I systematically categorize tasks and use AI differently for each type",
            5: "I have a clear framework for what to automate, augment, and keep human — and adjust it over time",
        },
    },
]

ESA_ANCHORS = {
    1: {"label": "Novice", "description": "I follow rules and instructions. I need someone to guide me through this. I can't handle unexpected situations."},
    2: {"label": "Developing", "description": "I recognize patterns from experience. I can handle routine situations but need guidance for complex ones. I'm building confidence."},
    3: {"label": "Proficient", "description": "I work independently and handle standard complexity. I know when to ask for help. I can explain my approach to others."},
    4: {"label": "Advanced", "description": "I handle exceptions and complexity. I mentor others in this area. I see connections others miss. I improve processes."},
    5: {"label": "Expert", "description": "I innovate in this field. I have deep intuition. I teach and shape how others approach this. I'm recognized for this expertise."},
}

ESA_VALIDATION_PROMPTS = {
    "low": "What's a recent situation where you needed help in this area?",
    "mid": "Describe a complex challenge you handled independently.",
    "high": "Give an example of how you've mentored others or innovated.",
}


# ── Score Computation ────────────────────────────────────────────────────────

def compute_adr(answers: dict[str, int]) -> dict:
    """Compute AI Dependency Risk score from Section A answers."""
    items = [answers.get(f"A{i}", 3) for i in range(1, 6)]
    raw = sum(items) / 5
    score = round(raw * 2)
    score = max(0, min(10, score))

    if score <= 3:
        level, response = "Low", "Light augmentation, expert acceleration"
    elif score <= 5:
        level, response = "Moderate", "Balanced approach, periodic cognitive forcing"
    elif score <= 7:
        level, response = "Elevated", "Regular cognitive forcing, active de-skilling monitoring"
    else:
        level, response = "High", "Heavy cognitive forcing, skill protection protocols, coaching emphasis"

    return {"score": score, "raw": round(raw, 2), "level": level, "pwa_response": response}


def compute_gp(answers: dict[str, int]) -> dict:
    """Compute Growth Potential score from Section B answers."""
    items = [answers.get(f"B{i}", 3) for i in range(1, 6)]
    raw = sum(items) / 5
    score = round(raw * 2)
    score = max(0, min(10, score))

    if score <= 3:
        level, response = "Low-engagement", "Focus on motivation, small wins, reduce overwhelm"
    elif score <= 5:
        level, response = "Developing", "Regular coaching, build habits, celebrate progress"
    elif score <= 7:
        level, response = "Active", "Full coaching, progressive challenges, skill tracking"
    else:
        level, response = "High-growth", "Advanced coaching, expert-track, leadership of learning"

    return {"score": score, "raw": round(raw, 2), "level": level, "pwa_response": response}


def compute_ali(answers: dict[str, int]) -> dict:
    """Compute AI Literacy Index from Section D answers."""
    items = [answers.get(f"D{i}", 3) for i in range(1, 5)]
    raw = sum(items) / 4
    score = round(raw * 2)
    score = max(0, min(10, score))

    if score <= 3:
        level = "Low"
    elif score <= 5:
        level = "Moderate"
    elif score <= 7:
        level = "Good"
    else:
        level = "High"

    return {"score": score, "raw": round(raw, 2), "level": level}


def compute_esa(domain_ratings: dict[str, int]) -> dict:
    """Compute Expertise Self-Assessment summary."""
    if not domain_ratings:
        return {"mean": 0, "domains": {}}

    ratings = list(domain_ratings.values())
    mean_rating = sum(ratings) / len(ratings)

    domains = {}
    for domain, rating in domain_ratings.items():
        label = ESA_ANCHORS.get(rating, {}).get("label", "Unknown")
        domains[domain] = {"rating": rating, "label": label}

    return {
        "mean": round(mean_rating, 2),
        "scaled": round(mean_rating * 2, 1),
        "domains": domains,
        "weak_domains": [d for d, r in domain_ratings.items() if r <= 2],
        "strong_domains": [d for d, r in domain_ratings.items() if r >= 4],
    }


def compute_pwri(adr_score: int, gp_score: int, ali_score: int, esa_mean: float) -> dict:
    """Compute the composite Pro Worker Readiness Index."""
    esa_scaled = esa_mean * 2  # Scale 1-5 to 0-10 range

    pwri = (
        (10 - adr_score) * 0.30
        + gp_score * 0.30
        + esa_scaled * 0.20
        + ali_score * 0.20
    )

    score = round(pwri)
    score = max(0, min(10, score))

    if score <= 3:
        label = "At Risk"
        meaning = "High dependency, low growth orientation. Focus: de-skilling recovery, motivation building"
    elif score <= 5:
        label = "Developing"
        meaning = "Mixed signals. Focus: build healthy AI habits, targeted coaching"
    elif score <= 7:
        label = "On Track"
        meaning = "Good balance. Focus: accelerate growth, deepen expertise"
    else:
        label = "Thriving"
        meaning = "Strong autonomy with effective AI use. Focus: expert acceleration, leadership"

    return {"score": score, "label": label, "meaning": meaning}


def compute_all_scores(answers: dict[str, int], domain_ratings: dict[str, int]) -> dict:
    """Compute all scores from raw assessment answers.

    Args:
        answers: Dict of item_id -> score, e.g. {"A1": 3, "A2": 4, "B1": 5, ...}
        domain_ratings: Dict of domain -> rating, e.g. {"Writing": 4, "Strategy": 3, ...}

    Returns:
        Complete scoring summary with all sub-scores and composite PWRI.
    """
    adr = compute_adr(answers)
    gp = compute_gp(answers)
    ali = compute_ali(answers)
    esa = compute_esa(domain_ratings)
    pwri = compute_pwri(adr["score"], gp["score"], ali["score"], esa["mean"])

    return {
        "adr": adr,
        "gp": gp,
        "ali": ali,
        "esa": esa,
        "pwri": pwri,
    }


# ── Calibration Matrix ──────────────────────────────────────────────────────

def compute_calibration(scores: dict, domain_ratings: dict[str, int]) -> dict:
    """Derive Pro Worker AI calibration settings from assessment scores.

    Implements the calibration matrix from the psychometric instrument.
    """
    adr = scores["adr"]["score"]
    gp = scores["gp"]["score"]
    ali = scores["ali"]["score"]
    weak_domains = scores["esa"].get("weak_domains", [])

    # Default calibration
    cal = {
        "default_friction_level": "medium",
        "cognitive_forcing_domains": [],
        "contrastive_explanation_domains": [],
        "automation_permissions": [],
        "coaching_frequency": "medium",
        "challenge_level": "medium",
        "feedback_style": "balanced",
        "explanation_depth": "frameworks",
    }

    # High dependency risk
    if adr >= 7:
        cal["default_friction_level"] = "high"
        cal["coaching_frequency"] = "every_interaction"
        cal["explanation_depth"] = "full"

    # High growth + low dependency
    if gp >= 7 and adr <= 4:
        cal["challenge_level"] = "high"
        cal["coaching_frequency"] = "high"

    # Low AI literacy
    if ali <= 3:
        cal["explanation_depth"] = "full"
        # Embed AI literacy coaching in every domain
        cal["contrastive_explanation_domains"] = list(domain_ratings.keys())

    # Weak domains get cognitive forcing
    for domain in weak_domains:
        if domain not in cal["cognitive_forcing_domains"]:
            cal["cognitive_forcing_domains"].append(domain)

    # Strong domains get automation permissions
    for domain in scores["esa"].get("strong_domains", []):
        if domain not in cal["automation_permissions"]:
            cal["automation_permissions"].append(domain)

    # Moderate dependency
    if 4 <= adr <= 6:
        cal["default_friction_level"] = "medium"
        cal["coaching_frequency"] = "high" if gp >= 6 else "medium"

    return cal


# ── Profile Generation ───────────────────────────────────────────────────────

def generate_profile_markdown(
    name: str,
    role: str,
    organization: str,
    industry: str,
    context_summary: str,
    scores: dict,
    domain_ratings: dict[str, int],
    calibration: dict,
    career_goals: list[str],
    skills_to_develop: list[str],
    skills_to_protect: list[str],
    tasks_automate: list[str],
    tasks_augment: list[str],
    tasks_coach: list[str],
    tasks_protect: list[str],
    tasks_hands_off: list[str],
    red_lines: list[str],
    learning_style: str = "balanced",
    feedback_style: str = "balanced",
    communication_style: str = "conversational",
) -> str:
    """Generate a complete Pro Worker AI profile as markdown.

    This is the full profile format matching profiles/TEMPLATE.md,
    generated from scored assessment data.
    """
    today = datetime.date.today().isoformat()

    # Build expertise table rows
    expertise_rows = []
    for domain, rating in domain_ratings.items():
        label = ESA_ANCHORS.get(rating, {}).get("label", "Unknown")
        growth = "Maintain"
        if domain in skills_to_develop:
            growth = f"**GROW to {min(rating + 1, 5)}** — targeted goal"
        elif domain in skills_to_protect:
            growth = "**PROTECT** — at risk from AI over-reliance"
        elif rating >= 4:
            growth = "Maintain — this is a core strength"
        expertise_rows.append(f"| {domain} | {rating} ({label}) | Self-assessed | {growth} |")

    expertise_table = "\n".join(expertise_rows)

    # Dependency risk analysis
    adr = scores["adr"]
    gp = scores["gp"]
    ali = scores["ali"]
    pwri = scores["pwri"]

    # Calibration YAML
    cf_domains = "\n".join(f"  - {d}" for d in calibration.get("cognitive_forcing_domains", []))
    ce_domains = "\n".join(f"  - {d}" for d in calibration.get("contrastive_explanation_domains", []))
    auto_perms = "\n".join(f"  - {d}" for d in calibration.get("automation_permissions", []))

    # Task lists
    def _task_list(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "- (none specified yet)"

    # Red lines
    red_lines_text = ""
    for i, rl in enumerate(red_lines, 1):
        red_lines_text += f"\n{i}. **{rl}**"

    profile = f"""# Pro Worker AI Profile — {name}

> Generated: {today}
> Last updated: {today}
> Assessment version: 2.0 (PWAQ)

---

## 1. Identity Card

| Field | Value |
|-------|-------|
| **Name** | {name} |
| **Role** | {role} |
| **Organization** | {organization} |
| **Industry** | {industry} |

**Context summary**: {context_summary}

---

## 2. Expertise Map

| Domain | Rating (1-5) | Evidence | Growth Direction |
|--------|-------------|----------|-----------------|
{expertise_table}

---

## 3. AI Relationship Status

**Dependency Risk Score**: {adr['score']}/10 — **{adr['level']}**
{adr['pwa_response']}

**AI Literacy Index**: {ali['score']}/10 — **{ali['level']}**

---

## 4. Growth Trajectory

**Growth Potential Score**: {gp['score']}/10 — **{gp['level']}**
{gp['pwa_response']}

**Pro Worker Readiness Index (PWRI)**: {pwri['score']}/10 — **{pwri['label']}**
{pwri['meaning']}

**Career goals (1-2 years)**:
{_task_list(career_goals)}

**Skills to develop**:
{_task_list(skills_to_develop)}

**Skills to protect** (at risk of atrophy):
{_task_list(skills_to_protect)}

---

## 5. Interaction Preferences

| Preference | Setting |
|-----------|---------|
| **Learning style** | {learning_style} |
| **Feedback style** | {feedback_style} |
| **Communication style** | {communication_style} |
| **Challenge tolerance** | {"High" if gp['score'] >= 7 else "Medium" if gp['score'] >= 4 else "Low"} |
| **Explanation depth** | {calibration.get('explanation_depth', 'frameworks')} |

---

## 6. Task Classification Matrix

### Automate (AI executes + annotates)
{_task_list(tasks_automate)}

### Augment (AI accelerates + challenges)
{_task_list(tasks_augment)}

### Coach (AI scaffolds + questions)
{_task_list(tasks_coach)}

### Protect (AI adds friction + teaches)
{_task_list(tasks_protect)}

### Hands-off (Human core)
{_task_list(tasks_hands_off)}

---

## 7. Pro-Worker Calibration Settings

```yaml
default_friction_level: {calibration.get('default_friction_level', 'medium')}
cognitive_forcing_domains:
{cf_domains if cf_domains else '  # (none)'}
contrastive_explanation_domains:
{ce_domains if ce_domains else '  # (none)'}
automation_permissions:
{auto_perms if auto_perms else '  # (none)'}
coaching_frequency: {calibration.get('coaching_frequency', 'medium')}
challenge_level: {calibration.get('challenge_level', 'medium')}
feedback_style: {calibration.get('feedback_style', 'balanced')}
explanation_depth: {calibration.get('explanation_depth', 'frameworks')}
```

---

## 8. Red Lines

Things this AI should NEVER do for {name}:
{red_lines_text if red_lines_text else "(To be determined after initial interactions)"}

---

## Assessment Scores (PWAQ v2.0)

| Metric | Score | Level |
|--------|-------|-------|
| AI Dependency Risk (ADR) | {adr['score']}/10 | {adr['level']} |
| Growth Potential (GP) | {gp['score']}/10 | {gp['level']} |
| AI Literacy Index (ALI) | {ali['score']}/10 | {ali['level']} |
| Expertise Mean (ESA) | {scores['esa']['mean']}/5 | — |
| **Pro Worker Readiness (PWRI)** | **{pwri['score']}/10** | **{pwri['label']}** |

---

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| {today} | Initial profile created via MCP assessment | proworker_assess |
"""
    return profile


# ── Assessment Protocol (for LLM consumption) ───────────────────────────────

def get_assessment_protocol() -> dict:
    """Return the full assessment protocol for the LLM to drive conversationally.

    The LLM receives this and uses it to ask questions one at a time,
    collect answers, then call the scoring and profile creation tools.
    """
    return {
        "protocol_version": "2.0",
        "instructions": (
            "You are running a Pro Worker AI assessment. Your job is to have a natural, "
            "conversational assessment with the user. Do NOT present this as a rigid survey. "
            "Instead, weave the questions into a genuine conversation about their work and "
            "how they use AI.\n\n"
            "FLOW:\n"
            "1. IDENTITY: Ask about their name, role, organization, industry. Get a sense of "
            "   their work context. (2-3 minutes)\n"
            "2. SECTION A — AI Dependency Risk: Ask the 5 questions naturally, one at a time. "
            "   For each, read the behavioral anchors and ask which best describes them. "
            "   They can pick a number 1-5 or describe their behavior and you infer the score. "
            "   (3-4 minutes)\n"
            "3. SECTION B — Growth Potential: Same approach, 5 questions. (3-4 minutes)\n"
            "4. SECTION D — AI Literacy: 4 questions. (2-3 minutes)\n"
            "5. EXPERTISE DOMAINS: Ask what domains/skills are most relevant to their work. "
            "   For each domain they name, ask them to rate themselves 1-5 using the ESA scale. "
            "   Validate with a behavioral example. Aim for 5-10 domains. (3-5 minutes)\n"
            "6. GOALS & CONTEXT: Ask about career goals, skills they want to develop, skills "
            "   they worry about losing to AI, tasks they want automated vs kept human. "
            "   Ask about their preferred learning style and feedback preferences. (3-4 minutes)\n"
            "7. SCORE & SAVE: Call proworker_assess_score with all collected answers, then "
            "   call proworker_assess_create_profile with the scores plus qualitative data. "
            "   Present the results to the user and ask if anything feels off.\n\n"
            "IMPORTANT GUIDELINES:\n"
            "- Be warm and conversational, not clinical\n"
            "- Explain WHY you're asking each question briefly\n"
            "- If the user gives a vague answer, probe with the behavioral anchors\n"
            "- It's OK to adjust scores based on behavioral evidence (expert interviewer mode)\n"
            "- The whole assessment should take 15-20 minutes\n"
            "- At the end, present scores and ask: 'Do these feel accurate? Anything you'd adjust?'"
        ),
        "sections": {
            "A": {
                "name": "AI Dependency Risk (ADR)",
                "description": "5 items measuring how dependent the user is on AI. Higher scores = greater risk of de-skilling.",
                "questions": SECTION_A_QUESTIONS,
            },
            "B": {
                "name": "Growth Potential (GP)",
                "description": "5 items measuring the user's growth orientation. Higher scores = more growth potential.",
                "questions": SECTION_B_QUESTIONS,
            },
            "D": {
                "name": "AI Literacy Index (ALI)",
                "description": "4 items measuring how well the user understands AI capabilities and limits.",
                "questions": SECTION_D_QUESTIONS,
            },
        },
        "esa": {
            "name": "Expertise Self-Assessment",
            "description": "Per-domain skill rating on a 1-5 behaviorally anchored scale.",
            "anchors": ESA_ANCHORS,
            "validation_prompts": ESA_VALIDATION_PROMPTS,
            "instructions": (
                "Ask the user to name the key skill domains in their work. "
                "For each domain, present the 5-level scale and ask them to rate themselves. "
                "Then ask a validation question based on their rating."
            ),
        },
        "qualitative": {
            "identity_fields": ["name", "role", "organization", "industry", "context_summary"],
            "goals_fields": ["career_goals", "skills_to_develop", "skills_to_protect"],
            "task_fields": ["tasks_automate", "tasks_augment", "tasks_coach", "tasks_protect", "tasks_hands_off"],
            "preference_fields": ["learning_style", "feedback_style", "communication_style"],
            "red_lines": "Ask: 'What should AI NEVER do for you? What tasks or outputs should always require your direct input?'",
        },
    }
