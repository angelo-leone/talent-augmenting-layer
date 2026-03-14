# Talent-Augmenting Layer — MCP Server

> Use your Talent-Augmenting Layer profile with ANY MCP-compatible client.
> Claude Code, Claude Desktop, Cursor, Windsurf, custom agents — anywhere.

---

## Quick Start

### 1. Install

```bash
cd mcp-server
pip install -e .
```

Or install dependencies directly:
```bash
pip install "mcp>=1.0.0" pyyaml
```

### 2. Test the server

```bash
cd mcp-server
python -m src.server
```

The server communicates over stdio (stdin/stdout), which is the standard MCP transport.

### 3. Connect to Claude Code

Add to your project's `.claude/settings.json` or `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "talent-augmenting-layer": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/talent-augmenting-layer/mcp-server",
      "env": {
        "TALENT_AUGMENTING_LAYER_PROFILES_DIR": "/path/to/talent-augmenting-layer/profiles"
      }
    }
  }
}
```

### 4. Connect to Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "talent-augmenting-layer": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/talent-augmenting-layer/mcp-server",
      "env": {
        "TALENT_AUGMENTING_LAYER_PROFILES_DIR": "/path/to/talent-augmenting-layer/profiles"
      }
    }
  }
}
```

### 5. Connect to any MCP client

The server is a standard MCP stdio server. Any client that supports MCP can connect using:
- **Command**: `python -m src.server`
- **Working directory**: The `mcp-server/` directory
- **Environment**: Set `TALENT_AUGMENTING_LAYER_PROFILES_DIR` to your profiles directory

---

## What's Exposed

### Tools (13 total)

**Assessment & Onboarding:**

| Tool | Purpose |
|------|---------|
| `talent_assess_start` | Start onboarding — returns full assessment protocol for chatbot-driven assessment |
| `talent_assess_score` | Compute all scores (ADR, GP, ALI, ESA, TALRI) from raw answers |
| `talent_assess_create_profile` | Generate and save a complete profile from assessment data |

**Profile Management:**

| Tool | Purpose |
|------|---------|
| `talent_get_profile` | Load a user's full profile (call at start of every conversation) |
| `talent_get_calibration` | Get compact calibration JSON for system prompt injection |
| `talent_save_profile` | Save or update a profile markdown file |
| `talent_delete_profile` | Delete a profile and its interaction logs |
| `talent_list_profiles` | List all available profiles |

**Runtime Behaviour:**

| Tool | Purpose |
|------|---------|
| `talent_classify_task` | Classify a task → automate/augment/coach/protect/hands-off |
| `talent_log_interaction` | Log an interaction for skill progression tracking |
| `talent_get_progression` | Get skill progression stats, trends, and de-skilling warnings |
| `talent_status` | Comprehensive status report (profile + progression + recommendations) |
| `talent_org_summary` | Organisation-level aggregation across all profiles |

### Resources

| URI | Content |
|-----|---------|
| `talent://profile/{name}` | Full profile markdown |
| `talent://system-prompt/{name}` | Complete system prompt (CLAUDE.md + profile) ready for any LLM |
| `talent://coaching-modules` | Structured coaching session modules |
| `talent://framework` | Assessment framework |
| `talent://literature` | Research literature backing |

### Prompts

| Prompt | Purpose |
|--------|---------|
| `talent-system` | Full system prompt for any LLM — paste into system instructions |
| `talent-assess` | Chatbot-driven onboarding assessment |
| `talent-coach` | Start a coaching session (optional: specify focus domain) |

---

## Usage Patterns

### Pattern 1: Claude Code (Full Integration)
The best experience. CLAUDE.md + slash commands + MCP server all work together.

```
# CLAUDE.md loads profile automatically
# Slash commands for assess/coach/update
# MCP server for tracking and cross-tool portability
```

### Pattern 2: Claude Desktop (Profile Injection)
Use the `talent-system` prompt or `talent_get_calibration` tool.

```
User: "Help me write an evaluation framework"
Claude: [calls talent_get_calibration(name="Angelo")]
Claude: [sees evaluation_design is a coaching domain]
Claude: "Before I draft anything — what's your initial approach to this evaluation?"
```

### Pattern 3: Any LLM via System Prompt
Use the `talent://system-prompt/{name}` resource to get a complete system prompt, then paste it into ChatGPT, Gemini, or any other LLM's system/custom instructions.

### Pattern 4: Custom Agents
Build agents that call `talent_classify_task` before acting:

```python
# Pseudocode for an agent that respects Talent-Augmenting Layer
task = user_input()
classification = mcp.call("talent_classify_task", name="Angelo", task_description=task)

if classification == "protect":
    ask_for_hypothesis_first()
elif classification == "coach":
    scaffold_dont_solve()
elif classification == "automate":
    execute_and_annotate()
```

### Pattern 5: Interaction Tracking
After each substantive interaction, log it:

```python
mcp.call("talent_log_interaction",
    name="Angelo",
    task_category="coach",
    domain="economic_analysis",
    engagement_level="active",
    skill_signal="growth",
    notes="User identified counterfactual without prompting"
)
```

Then check progression:
```python
stats = mcp.call("talent_get_progression", name="Angelo")
# Returns: domain signals, engagement distribution, atrophy warnings
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TALENT_AUGMENTING_LAYER_PROFILES_DIR` | `../profiles/` | Directory where profile `.md` files are stored |

---

## Chatbot-Driven Onboarding

The assessment is embedded directly in the MCP server. Any chatbot connected via MCP can run the full onboarding:

```
1. Chatbot calls talent_assess_start()
   → Gets full question bank + conversational instructions

2. Chatbot asks questions one at a time, naturally
   → Collects scores (1-5) for each TALQ item
   → Collects domain expertise ratings

3. Chatbot calls talent_assess_score(answers, domain_ratings)
   → Gets computed ADR, GP, ALI, ESA, TALRI scores

4. Chatbot calls talent_assess_create_profile(name, scores, demographics, goals, ...)
   → Profile is generated and saved to disk
   → Future conversations auto-load the profile
```

No web UI needed. No separate forms. The chatbot IS the assessment interface.

---

## Architecture

```
mcp-server/
├── pyproject.toml          # Package config & dependencies
├── README.md               # This file
└── src/
    ├── __init__.py
    ├── server.py           # MCP server — tools, resources, prompts
    ├── profile_manager.py  # Profile CRUD, parsing, interaction logging
    └── assessment.py       # Embedded assessment engine (questions, scoring, profile generation)
```

The server reads profiles from markdown files and the CLAUDE.md system prompt from the parent repo. Interaction logs are stored as JSONL files alongside profiles.

For comprehensive platform-specific integration guides, see `docs/integration-guide.md`.
