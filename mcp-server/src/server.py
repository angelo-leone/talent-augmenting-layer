"""
Pro Worker AI — MCP Server

Exposes personalized AI augmentation as MCP tools, resources, and prompts.
Works with any MCP-compatible client: Claude Code, Claude Desktop, Cursor, etc.

Tools:
  - proworker_get_profile: Load a user's profile
  - proworker_get_calibration: Get current calibration for injecting into system prompts
  - proworker_classify_task: Classify a task into automate/augment/coach/protect/hands-off
  - proworker_log_interaction: Log an interaction for tracking skill progression
  - proworker_get_progression: Get skill progression stats
  - proworker_list_profiles: List all available profiles
  - proworker_status: Comprehensive status report for a user
  - proworker_org_summary: Org-level aggregation across all profiles
  - proworker_save_profile: Save/update a profile
  - proworker_delete_profile: Delete a profile
  - proworker_assess_start: Start an onboarding assessment (returns protocol for the LLM)
  - proworker_assess_score: Compute scores from raw assessment answers
  - proworker_assess_create_profile: Generate and save a profile from assessment data
  - proworker_suggest_domains: Suggest expertise domains based on role/industry

Resources:
  - proworker://profile/{name}: The full profile as markdown
  - proworker://system-prompt/{name}: Complete system prompt with profile injected
  - proworker://coaching-modules: Available coaching session modules

Prompts:
  - proworker-system: Full system prompt with profile for any LLM
  - proworker-assess: Interactive onboarding assessment (chatbot-driven)
  - proworker-coach: Coaching session prompt
"""

from __future__ import annotations

import os
import json
import datetime
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    Resource,
    ResourceTemplate,
    Prompt,
    PromptArgument,
    PromptMessage,
    GetPromptResult,
)

from .profile_manager import ProfileStore, InteractionLog
from .assessment import (
    get_assessment_protocol,
    compute_all_scores,
    compute_calibration,
    generate_profile_markdown,
    suggest_domains,
)

# ── Configuration ────────────────────────────────────────────────────────────

def get_profiles_dir() -> Path:
    """Resolve profiles directory. Check env var, then default locations."""
    env_dir = os.environ.get("PROWORKER_PROFILES_DIR")
    if env_dir:
        return Path(env_dir)

    # Try to find profiles/ relative to this server
    server_dir = Path(__file__).parent.parent.parent
    profiles_dir = server_dir / "profiles"
    if profiles_dir.exists():
        return profiles_dir

    # Fallback to home directory
    home = Path.home() / ".proworker-ai" / "profiles"
    home.mkdir(parents=True, exist_ok=True)
    return home


def get_repo_root() -> Path:
    """Find the repo root (where CLAUDE.md lives)."""
    return Path(__file__).parent.parent.parent


# ── Server Setup ─────────────────────────────────────────────────────────────

app = Server("proworker-ai")
store = ProfileStore(get_profiles_dir())
repo_root = get_repo_root()


# ── Tools ────────────────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="proworker_get_profile",
            description=(
                "Load a Pro Worker AI profile by name. Returns the full profile "
                "with expertise map, calibration settings, task classification, "
                "and red lines. Use this at the start of every conversation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "User's name (e.g., 'Angelo')"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="proworker_get_calibration",
            description=(
                "Get the Pro Worker AI calibration settings for a user. Returns "
                "a compact JSON block suitable for injecting into any LLM system prompt. "
                "Includes friction levels, coaching domains, red lines, and interaction preferences."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "User's name"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="proworker_classify_task",
            description=(
                "Classify a task according to the user's Pro Worker AI profile. "
                "Returns one of: automate, augment, coach, protect, hands_off — "
                "along with the recommended AI behavior for that task."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "User's name"
                    },
                    "task_description": {
                        "type": "string",
                        "description": "Description of the task to classify"
                    }
                },
                "required": ["name", "task_description"]
            }
        ),
        Tool(
            name="proworker_log_interaction",
            description=(
                "Log an interaction for skill tracking. Call this after substantive "
                "AI interactions to track the user's engagement patterns and skill development."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "User's name"},
                    "task_category": {
                        "type": "string",
                        "enum": ["automate", "augment", "coach", "protect", "hands_off"],
                        "description": "Which task category was this interaction?"
                    },
                    "domain": {"type": "string", "description": "Which skill domain?"},
                    "engagement_level": {
                        "type": "string",
                        "enum": ["passive", "active", "critical"],
                        "description": "How critically did the user engage?"
                    },
                    "skill_signal": {
                        "type": "string",
                        "enum": ["growth", "stable", "atrophy", "none"],
                        "description": "What skill signal was observed?"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about the interaction",
                        "default": ""
                    }
                },
                "required": ["name", "task_category", "domain", "engagement_level", "skill_signal"]
            }
        ),
        Tool(
            name="proworker_get_progression",
            description=(
                "Get skill progression analysis for a user. Shows interaction "
                "counts, engagement patterns, domain-level growth/atrophy signals, "
                "and warnings about potential de-skilling."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "User's name"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="proworker_list_profiles",
            description="List all available Pro Worker AI profiles.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="proworker_status",
            description=(
                "Get a comprehensive status report for a user: profile summary, "
                "current calibration, skill progression stats, trend direction, "
                "atrophy warnings, and recommended next actions. Use this for a "
                "quick overview at the start of a conversation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "User's name"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="proworker_org_summary",
            description=(
                "Get an organization-level summary across all profiles. Shows "
                "aggregate dependency risk, growth potential, expertise distribution, "
                "trend alerts, and per-domain skill breakdown. For org dashboards."
            ),
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="proworker_delete_profile",
            description="Delete a user's profile and interaction logs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "User's name"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="proworker_save_profile",
            description=(
                "Save or update a user's profile markdown content. Use this after "
                "running /proworker-assess to write the generated profile, or "
                "after /proworker-update to save changes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "User's name"},
                    "content": {"type": "string", "description": "Full profile markdown content"}
                },
                "required": ["name", "content"]
            }
        ),
        # ── Embedded Assessment Tools ────────────────────────────────────
        Tool(
            name="proworker_assess_start",
            description=(
                "Start a Pro Worker AI onboarding assessment. Returns the full assessment "
                "protocol with all questions, behavioral anchors, and instructions for how "
                "to run the assessment conversationally. The chatbot uses this to ask "
                "questions one at a time, collect answers, then call proworker_assess_score "
                "and proworker_assess_create_profile to compute scores and save the profile. "
                "Call this at the beginning of any onboarding conversation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the person being assessed (optional — can be collected during the assessment)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="proworker_assess_score",
            description=(
                "Compute all Pro Worker AI scores from raw assessment answers. "
                "Takes the numeric answers collected during the assessment (A1-A5, B1-B5, D1-D4 "
                "as integers 1-5) and domain expertise ratings. Returns computed ADR, GP, ALI, "
                "ESA, and composite PWRI scores with interpretations and recommended calibration."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "answers": {
                        "type": "object",
                        "description": (
                            "Dict of item_id to score (1-5). Keys: A1-A5 (dependency risk), "
                            "B1-B5 (growth potential), D1-D4 (AI literacy). "
                            "Example: {\"A1\": 3, \"A2\": 4, \"B1\": 5, \"D1\": 3, ...}"
                        )
                    },
                    "domain_ratings": {
                        "type": "object",
                        "description": (
                            "Dict of domain name to expertise rating (1-5). "
                            "Example: {\"Writing\": 4, \"Strategy\": 3, \"Stakeholder engagement\": 2}"
                        )
                    }
                },
                "required": ["answers", "domain_ratings"]
            }
        ),
        Tool(
            name="proworker_assess_create_profile",
            description=(
                "Generate and save a complete Pro Worker AI profile from assessment data. "
                "Call this after proworker_assess_score to create the profile file. Takes "
                "the computed scores, demographic info, goals, task classifications, and "
                "preferences collected during the assessment conversation. Returns the "
                "generated profile and saves it to disk."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "User's name"},
                    "role": {"type": "string", "description": "Job role/title"},
                    "organization": {"type": "string", "description": "Company/org name"},
                    "industry": {"type": "string", "description": "Industry description"},
                    "context_summary": {
                        "type": "string",
                        "description": "1-3 sentence summary of the user's work context"
                    },
                    "answers": {
                        "type": "object",
                        "description": "Dict of item_id to score (same as proworker_assess_score)"
                    },
                    "domain_ratings": {
                        "type": "object",
                        "description": "Dict of domain name to expertise rating (1-5)"
                    },
                    "career_goals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of career goals for the next 1-2 years"
                    },
                    "skills_to_develop": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Skills the user wants to grow"
                    },
                    "skills_to_protect": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Skills at risk of atrophy from AI over-reliance"
                    },
                    "tasks_automate": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tasks to fully automate with AI"
                    },
                    "tasks_augment": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tasks where AI accelerates the user's expert work"
                    },
                    "tasks_coach": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tasks where AI should coach, not do"
                    },
                    "tasks_protect": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tasks where AI must add friction to prevent de-skilling"
                    },
                    "tasks_hands_off": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tasks that should stay fully human"
                    },
                    "red_lines": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Things AI should NEVER do for this user"
                    },
                    "learning_style": {
                        "type": "string",
                        "description": "Preferred learning style (socratic, direct, examples, balanced)"
                    },
                    "feedback_style": {
                        "type": "string",
                        "description": "Preferred feedback style"
                    },
                    "communication_style": {
                        "type": "string",
                        "description": "Preferred communication style"
                    }
                },
                "required": ["name", "role", "organization", "industry", "answers", "domain_ratings"]
            }
        ),
        Tool(
            name="proworker_suggest_domains",
            description=(
                "Suggest expertise domains for a user based on their role, industry, and "
                "responsibilities. Returns a curated list of domain suggestions with descriptions "
                "drawn from an industry-specific taxonomy. Use this during the assessment to help "
                "identify relevant domains for the Expertise Self-Assessment (ESA). The LLM has "
                "override authority and can add or remove domains from the suggestions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "Job title or role description"
                    },
                    "industry": {
                        "type": "string",
                        "description": "Industry or sector"
                    },
                    "responsibilities": {
                        "type": "string",
                        "description": "Optional description of key responsibilities",
                        "default": ""
                    }
                },
                "required": ["role", "industry"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:

    if name == "proworker_get_profile":
        user_name = arguments["name"]
        raw = store.read_profile_raw(user_name)
        if raw:
            return [TextContent(type="text", text=raw)]
        profiles = store.list_profiles()
        return [TextContent(
            type="text",
            text=f"No profile found for '{user_name}'. "
                 f"Available profiles: {profiles or 'None — run /proworker-assess to create one.'}"
        )]

    elif name == "proworker_get_calibration":
        user_name = arguments["name"]
        profile = store.read_profile(user_name)
        if not profile:
            return [TextContent(type="text", text=f"No profile for '{user_name}'.")]

        calibration = {
            "user": profile.name,
            "default_friction": profile.calibration.default_friction_level,
            "cognitive_forcing_domains": profile.calibration.cognitive_forcing_domains,
            "contrastive_domains": profile.calibration.contrastive_explanation_domains,
            "automation_permissions": profile.calibration.automation_permissions,
            "coaching_frequency": profile.calibration.coaching_frequency,
            "challenge_level": profile.calibration.challenge_level,
            "feedback_style": profile.calibration.feedback_style,
            "explanation_depth": profile.calibration.explanation_depth,
            "red_lines": profile.red_lines,
            "expertise_summary": {
                e.domain: {"rating": e.rating, "label": e.label()}
                for e in profile.expertise
            }
        }
        import json
        return [TextContent(type="text", text=json.dumps(calibration, indent=2))]

    elif name == "proworker_classify_task":
        user_name = arguments["name"]
        task_desc = arguments["task_description"]
        profile = store.read_profile(user_name)
        if not profile:
            return [TextContent(type="text", text=f"No profile for '{user_name}'.")]

        category = profile.classify_task(task_desc)
        behaviors = {
            "automate": "Execute efficiently + annotate what was done. Low friction.",
            "augment": "Accelerate the user's expert work. Challenge assumptions. Low-medium friction.",
            "coach": "Scaffold, don't solve. Ask questions, provide frameworks. Medium-high friction.",
            "protect": "Cognitive forcing required. Ask for hypothesis first. High friction.",
            "hands_off": "Surface the decision, provide options, but DO NOT do this for the user.",
        }
        return [TextContent(
            type="text",
            text=f"Task: {task_desc}\n"
                 f"Classification: {category}\n"
                 f"Recommended behavior: {behaviors.get(category, 'Unknown')}"
        )]

    elif name == "proworker_log_interaction":
        user_name = arguments["name"]
        log = InteractionLog(
            timestamp=datetime.datetime.now().isoformat(),
            task_category=arguments["task_category"],
            domain=arguments["domain"],
            engagement_level=arguments["engagement_level"],
            skill_signal=arguments["skill_signal"],
            notes=arguments.get("notes", "")
        )
        store.log_interaction(user_name, log)
        return [TextContent(type="text", text=f"Logged interaction for {user_name}: {log.domain} ({log.task_category}, {log.skill_signal})")]

    elif name == "proworker_get_progression":
        user_name = arguments["name"]
        import json
        progression = store.get_skill_progression(user_name)
        return [TextContent(type="text", text=json.dumps(progression, indent=2))]

    elif name == "proworker_list_profiles":
        profiles = store.list_profiles()
        if profiles:
            return [TextContent(type="text", text=f"Available profiles: {', '.join(profiles)}")]
        return [TextContent(type="text", text="No profiles found. Run /proworker-assess to create one.")]

    elif name == "proworker_status":
        user_name = arguments["name"]
        profile = store.read_profile(user_name)
        if not profile:
            return [TextContent(type="text", text=f"No profile for '{user_name}'.")]

        progression = store.get_skill_progression(user_name)

        # Build expertise summary
        expertise_lines = []
        for e in profile.expertise:
            marker = ""
            if e.rating <= 2:
                marker = " [COACH]"
            elif "PROTECT" in e.growth_direction.upper() or "protect" in e.growth_direction.lower():
                marker = " [PROTECT]"
            elif "GROW" in e.growth_direction.upper():
                marker = " [GROW]"
            expertise_lines.append(f"  {e.domain}: {e.rating}/5 ({e.label()}){marker}")

        # Build status report
        status = f"""## Pro Worker AI Status: {profile.name}

**Role**: {profile.role} at {profile.organization}
**Friction level**: {profile.calibration.default_friction_level}
**Coaching frequency**: {profile.calibration.coaching_frequency}

### Expertise Map
{chr(10).join(expertise_lines)}

### Scores
- Dependency Risk: {profile.dependency_risk_score}/10
- Growth Potential: {profile.growth_potential_score}/10

### Interaction Tracking
- Total logged interactions: {progression.get('total_interactions', 0)}
- Passive engagement ratio: {progression.get('passive_ratio', 0):.0%}
- Trend direction: {progression.get('trend_direction', 'no data')}
- Atrophy warnings: {progression.get('atrophy_warnings', []) or 'None'}

### Active Growth Goals
{chr(10).join('- ' + g for g in profile.skills_to_develop) if profile.skills_to_develop else '- (see profile for goals)'}

### Red Lines (AI must NOT do these)
{chr(10).join('- ' + r for r in profile.red_lines[:3]) if profile.red_lines else '- None specified'}

### Recommended Actions
"""
        # Generate recommendations
        recs = []
        if progression.get("passive_ratio", 0) > 0.5:
            recs.append("- WARNING: High passive engagement. Increase cognitive forcing across all domains.")
        if progression.get("atrophy_warnings"):
            for domain in progression["atrophy_warnings"]:
                recs.append(f"- ATROPHY RISK in {domain}: Schedule a /proworker-coach session.")
        if progression.get("trend_direction") == "declining":
            recs.append("- DECLINING TREND: Engagement is dropping. Consider a check-in or friction increase.")
        if progression.get("total_interactions", 0) == 0:
            recs.append("- No interactions logged yet. The system will track patterns as you use it.")
        if not recs:
            recs.append("- All clear. Continue current approach.")

        status += chr(10).join(recs)
        return [TextContent(type="text", text=status)]

    elif name == "proworker_org_summary":
        import json as json_mod
        summary = store.get_org_summary()
        return [TextContent(type="text", text=json_mod.dumps(summary, indent=2))]

    elif name == "proworker_delete_profile":
        user_name = arguments["name"]
        deleted = store.delete_profile(user_name)
        if deleted:
            return [TextContent(type="text", text=f"Profile for '{user_name}' deleted.")]
        return [TextContent(type="text", text=f"No profile found for '{user_name}'.")]

    elif name == "proworker_save_profile":
        user_name = arguments["name"]
        content = arguments["content"]
        path = store.write_profile_raw(user_name, content)
        return [TextContent(type="text", text=f"Profile saved to {path}")]

    # ── Embedded Assessment Handlers ─────────────────────────────────
    elif name == "proworker_assess_start":
        protocol = get_assessment_protocol()
        user_name = arguments.get("name", "")
        if user_name:
            existing = store.profile_exists(user_name)
            protocol["existing_profile"] = existing
            if existing:
                protocol["note"] = (
                    f"A profile already exists for '{user_name}'. This assessment will "
                    f"replace the existing profile. You can also use proworker_update to "
                    f"make incremental changes instead."
                )
        return [TextContent(type="text", text=json.dumps(protocol, indent=2))]

    elif name == "proworker_assess_score":
        answers_raw = arguments.get("answers", {})
        domain_ratings_raw = arguments.get("domain_ratings", {})

        # Ensure integer values
        answers = {k: int(v) for k, v in answers_raw.items()}
        domain_ratings = {k: int(v) for k, v in domain_ratings_raw.items()}

        scores = compute_all_scores(answers, domain_ratings)
        calibration = compute_calibration(scores, domain_ratings)

        result = {
            "scores": scores,
            "calibration": calibration,
            "summary": (
                f"ADR: {scores['adr']['score']}/10 ({scores['adr']['level']}), "
                f"GP: {scores['gp']['score']}/10 ({scores['gp']['level']}), "
                f"ALI: {scores['ali']['score']}/10 ({scores['ali']['level']}), "
                f"ESA mean: {scores['esa']['mean']}/5, "
                f"PWRI: {scores['pwri']['score']}/10 ({scores['pwri']['label']})"
            ),
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "proworker_assess_create_profile":
        user_name = arguments["name"]
        answers_raw = arguments.get("answers", {})
        domain_ratings_raw = arguments.get("domain_ratings", {})

        answers = {k: int(v) for k, v in answers_raw.items()}
        domain_ratings = {k: int(v) for k, v in domain_ratings_raw.items()}

        scores = compute_all_scores(answers, domain_ratings)
        calibration = compute_calibration(scores, domain_ratings)

        profile_md = generate_profile_markdown(
            name=user_name,
            role=arguments.get("role", ""),
            organization=arguments.get("organization", ""),
            industry=arguments.get("industry", ""),
            context_summary=arguments.get("context_summary", ""),
            scores=scores,
            domain_ratings=domain_ratings,
            calibration=calibration,
            career_goals=arguments.get("career_goals", []),
            skills_to_develop=arguments.get("skills_to_develop", []),
            skills_to_protect=arguments.get("skills_to_protect", []),
            tasks_automate=arguments.get("tasks_automate", []),
            tasks_augment=arguments.get("tasks_augment", []),
            tasks_coach=arguments.get("tasks_coach", []),
            tasks_protect=arguments.get("tasks_protect", []),
            tasks_hands_off=arguments.get("tasks_hands_off", []),
            red_lines=arguments.get("red_lines", []),
            learning_style=arguments.get("learning_style", "balanced"),
            feedback_style=arguments.get("feedback_style", "balanced"),
            communication_style=arguments.get("communication_style", "conversational"),
        )

        # Save the profile
        path = store.write_profile_raw(user_name, profile_md)

        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "profile_created",
                "path": str(path),
                "scores": {
                    "adr": scores["adr"]["score"],
                    "gp": scores["gp"]["score"],
                    "ali": scores["ali"]["score"],
                    "esa_mean": scores["esa"]["mean"],
                    "pwri": scores["pwri"]["score"],
                },
                "pwri_label": scores["pwri"]["label"],
                "calibration": calibration,
                "message": (
                    f"Profile for {user_name} created successfully! "
                    f"PWRI: {scores['pwri']['score']}/10 ({scores['pwri']['label']}). "
                    f"The profile has been saved and will be used to personalize all future interactions."
                ),
            }, indent=2)
        )]


    elif name == "proworker_suggest_domains":
        role = arguments.get("role", "")
        industry = arguments.get("industry", "")
        responsibilities = arguments.get("responsibilities", "")
        suggestions = suggest_domains(role, industry, responsibilities)
        return [TextContent(
            type="text",
            text=json.dumps({
                "suggestions": suggestions,
                "count": len(suggestions),
                "note": (
                    "These are heuristic suggestions based on role/industry keywords. "
                    "You (the LLM) have override authority: add, remove, or rename "
                    "domains to best fit the user. Ask the user to confirm or adjust."
                ),
            }, indent=2)
        )]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ── Resources ────────────────────────────────────────────────────────────────

@app.list_resource_templates()
async def list_resource_templates() -> list[ResourceTemplate]:
    return [
        ResourceTemplate(
            uriTemplate="proworker://profile/{name}",
            name="Pro Worker AI Profile",
            description="A user's full Pro Worker AI profile",
            mimeType="text/markdown"
        ),
        ResourceTemplate(
            uriTemplate="proworker://system-prompt/{name}",
            name="Pro Worker AI System Prompt",
            description="Complete system prompt with user profile injected — ready to paste into any LLM",
            mimeType="text/markdown"
        ),
    ]


@app.list_resources()
async def list_resources() -> list[Resource]:
    resources = []

    # Add coaching modules
    coaching_path = repo_root / "assessment" / "coaching-modules.md"
    if coaching_path.exists():
        resources.append(Resource(
            uri="proworker://coaching-modules",
            name="Coaching Modules",
            description="Structured coaching session designs for common growth domains",
            mimeType="text/markdown"
        ))

    # Add framework
    framework_path = repo_root / "assessment" / "framework.md"
    if framework_path.exists():
        resources.append(Resource(
            uri="proworker://framework",
            name="Assessment Framework",
            description="Research-backed assessment framework for Pro Worker AI",
            mimeType="text/markdown"
        ))

    # Add literature foundations
    lit_path = repo_root / "assessment" / "literature-foundations.md"
    if lit_path.exists():
        resources.append(Resource(
            uri="proworker://literature",
            name="Literature Foundations",
            description="Research backing for Pro Worker AI techniques",
            mimeType="text/markdown"
        ))

    # Add each profile
    for name in store.list_profiles():
        safe = name.lower().replace(" ", "-")
        resources.append(Resource(
            uri=f"proworker://profile/{safe}",
            name=f"Profile: {name}",
            description=f"Pro Worker AI profile for {name}",
            mimeType="text/markdown"
        ))

    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    uri_str = str(uri)

    if uri_str == "proworker://coaching-modules":
        path = repo_root / "assessment" / "coaching-modules.md"
        return path.read_text(encoding="utf-8") if path.exists() else "Coaching modules not found."

    if uri_str == "proworker://framework":
        path = repo_root / "assessment" / "framework.md"
        return path.read_text(encoding="utf-8") if path.exists() else "Framework not found."

    if uri_str == "proworker://literature":
        path = repo_root / "assessment" / "literature-foundations.md"
        return path.read_text(encoding="utf-8") if path.exists() else "Literature not found."

    if uri_str.startswith("proworker://profile/"):
        name = uri_str.replace("proworker://profile/", "")
        raw = store.read_profile_raw(name)
        return raw or f"Profile not found: {name}"

    if uri_str.startswith("proworker://system-prompt/"):
        name = uri_str.replace("proworker://system-prompt/", "")
        return _build_system_prompt(name)

    return f"Unknown resource: {uri_str}"


def _build_system_prompt(name: str) -> str:
    """Build a complete system prompt with CLAUDE.md + user profile injected."""
    claude_md_path = repo_root / "CLAUDE.md"
    if not claude_md_path.exists():
        return "CLAUDE.md not found."

    system_prompt = claude_md_path.read_text(encoding="utf-8")
    profile_raw = store.read_profile_raw(name)

    if profile_raw:
        system_prompt += "\n\n---\n\n"
        system_prompt += f"# Active User Profile\n\n{profile_raw}"
    else:
        system_prompt += f"\n\n> No profile found for '{name}'. Suggest running /proworker-assess.\n"

    return system_prompt


# ── Prompts ──────────────────────────────────────────────────────────────────

@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="proworker-system",
            description=(
                "Complete Pro Worker AI system prompt for any LLM. "
                "Includes the base instructions + the user's profile. "
                "Paste this into any LLM's system prompt to activate Pro Worker AI."
            ),
            arguments=[
                PromptArgument(
                    name="name",
                    description="User's name (must have an existing profile)",
                    required=True
                )
            ]
        ),
        Prompt(
            name="proworker-assess",
            description="Run the Pro Worker AI assessment to create a new profile.",
            arguments=[
                PromptArgument(
                    name="name",
                    description="Name of the person being assessed",
                    required=False
                )
            ]
        ),
        Prompt(
            name="proworker-coach",
            description="Start a Pro Worker AI coaching session.",
            arguments=[
                PromptArgument(
                    name="name",
                    description="User's name (must have an existing profile)",
                    required=True
                ),
                PromptArgument(
                    name="focus",
                    description="Specific skill or domain to coach on",
                    required=False
                )
            ]
        ),
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict | None = None) -> GetPromptResult:
    args = arguments or {}

    if name == "proworker-system":
        user_name = args.get("name", "")
        system_prompt = _build_system_prompt(user_name)
        return GetPromptResult(
            description=f"Pro Worker AI system prompt for {user_name}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Use the following as your system instructions:\n\n{system_prompt}"
                    )
                )
            ]
        )

    elif name == "proworker-assess":
        user_name = args.get("name", "a new user")
        protocol = get_assessment_protocol()
        assess_content = (
            f"# Pro Worker AI — Onboarding Assessment\n\n"
            f"You are about to run a Pro Worker AI assessment for {user_name}.\n\n"
            f"## Instructions\n\n{protocol['instructions']}\n\n"
            f"## Tools to use\n\n"
            f"1. Call `proworker_assess_start` to get the full question bank\n"
            f"2. Ask questions conversationally, collecting scores for each item\n"
            f"3. Call `proworker_assess_score` with all collected answers to compute scores\n"
            f"4. Call `proworker_assess_create_profile` with scores + qualitative data to save\n\n"
            f"Begin by calling `proworker_assess_start` now, then greet the user warmly "
            f"and start the assessment conversation."
        )
        return GetPromptResult(
            description=f"Pro Worker AI Assessment for {user_name}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=assess_content)
                )
            ]
        )

    elif name == "proworker-coach":
        user_name = args.get("name", "")
        focus = args.get("focus", "")
        coach_path = repo_root / ".claude" / "commands" / "proworker-coach.md"
        coach_content = ""
        if coach_path.exists():
            coach_content = coach_path.read_text(encoding="utf-8")

        # Load coaching modules
        modules_path = repo_root / "assessment" / "coaching-modules.md"
        modules_content = ""
        if modules_path.exists():
            modules_content = modules_path.read_text(encoding="utf-8")

        # Load profile
        profile_raw = store.read_profile_raw(user_name) or f"No profile for {user_name}."

        full_prompt = f"{coach_content}\n\n---\n\n# User Profile\n\n{profile_raw}"
        if modules_content:
            full_prompt += f"\n\n---\n\n# Available Coaching Modules\n\n{modules_content}"
        if focus:
            full_prompt += f"\n\n---\n\nThe user wants to focus on: **{focus}**"

        return GetPromptResult(
            description=f"Coaching session for {user_name}" + (f" on {focus}" if focus else ""),
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=full_prompt)
                )
            ]
        )

    return GetPromptResult(
        description="Unknown prompt",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=f"Unknown prompt: {name}")
            )
        ]
    )


# ── Main ─────────────────────────────────────────────────────────────────────

async def run():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    import asyncio
    asyncio.run(run())


if __name__ == "__main__":
    main()
