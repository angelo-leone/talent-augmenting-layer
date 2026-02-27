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

Resources:
  - proworker://profile/{name}: The full profile as markdown
  - proworker://system-prompt/{name}: Complete system prompt with profile injected
  - proworker://coaching-modules: Available coaching session modules

Prompts:
  - proworker-system: Full system prompt with profile for any LLM
  - proworker-assess: Assessment prompt
  - proworker-coach: Coaching session prompt
"""

from __future__ import annotations

import os
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
        assess_path = repo_root / ".claude" / "commands" / "proworker-assess.md"
        assess_content = ""
        if assess_path.exists():
            assess_content = assess_path.read_text(encoding="utf-8")
        else:
            assess_content = (
                "Run the Pro Worker AI assessment. Ask the user about their role, "
                "expertise, AI usage, goals, preferences, and tasks. Generate a profile "
                "in profiles/pro-{name}.md."
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
