# Pro Worker AI — Integration Guide

> How to use Pro Worker AI with any LLM, agent, or tool.
> The portability story is the product differentiator.

---

## Architecture Overview

Pro Worker AI has three layers that can be used independently or together:

```
Layer 1: CLAUDE.md (system instructions)
  → Works in Claude Code natively
  → Can be pasted into any LLM's system prompt

Layer 2: MCP Server (cross-platform tools)
  → Works with any MCP client (Claude Code, Desktop, Cursor, Windsurf, etc.)
  → Exposes tools, resources, and prompts over stdio
  → Handles onboarding assessment, scoring, profile CRUD, and tracking

Layer 3: Profiles (pro-{name}.md files)
  → Portable markdown files containing the user's configuration
  → Can be read by any system — no proprietary format
```

---

## Platform Integrations

### 1. Claude Code (Full Integration)

**Best experience.** All three layers work together natively.

**Setup:**
1. Clone the repo into your project (or as a standalone directory)
2. Add the MCP server to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "proworker-ai": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/pro-worker-ai/mcp-server",
      "env": {
        "PROWORKER_PROFILES_DIR": "/path/to/pro-worker-ai/profiles"
      }
    }
  }
}
```

3. CLAUDE.md is automatically loaded from the repo root
4. Slash commands (`/proworker-assess`, `/proworker-coach`, `/proworker-update`) are available in `.claude/commands/`

**Onboarding a new user:**
- Type `/proworker-assess` OR the chatbot calls `proworker_assess_start` via MCP
- The chatbot asks questions conversationally
- Scores are computed server-side via `proworker_assess_score`
- Profile is saved via `proworker_assess_create_profile`
- Future conversations auto-load the profile from CLAUDE.md instructions

**Day-to-day use:**
- CLAUDE.md instructs the AI to load the user's profile at conversation start
- The AI checks the profile to calibrate friction, coaching, and automation
- Interactions can be logged via `proworker_log_interaction` for skill tracking

---

### 2. Claude Desktop

**Setup:**
1. Install the MCP server:
```bash
cd pro-worker-ai/mcp-server
pip install -e .
```

2. Add to `claude_desktop_config.json` (find it in Claude Desktop settings):
```json
{
  "mcpServers": {
    "proworker-ai": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/pro-worker-ai/mcp-server",
      "env": {
        "PROWORKER_PROFILES_DIR": "/path/to/pro-worker-ai/profiles"
      }
    }
  }
}
```

3. Restart Claude Desktop

**Onboarding:**
- Use the `proworker-assess` prompt from the MCP server
- Or manually call `proworker_assess_start` to get the assessment protocol
- The chatbot will guide you through the questions and create your profile

**Usage:**
- At the start of each conversation, Claude can call `proworker_get_profile` or `proworker_get_calibration`
- For full system prompt injection, use the `proworker-system` prompt
- The AI adapts its behavior based on your profile

---

### 3. Cursor / Windsurf / Other MCP Editors

**Setup (same as any MCP client):**

For **Cursor**, add to `.cursor/mcp.json` or Cursor settings:
```json
{
  "mcpServers": {
    "proworker-ai": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/pro-worker-ai/mcp-server",
      "env": {
        "PROWORKER_PROFILES_DIR": "/path/to/pro-worker-ai/profiles"
      }
    }
  }
}
```

For **Windsurf**, add to the MCP server configuration in settings.

**Usage pattern:**
1. At conversation start, call `proworker_get_calibration(name="YourName")`
2. The returned calibration tells the AI how to behave
3. Before acting on a task, call `proworker_classify_task(name, task_description)` to determine the right approach
4. After interactions, log them with `proworker_log_interaction`

---

### 4. ChatGPT (Custom Instructions)

ChatGPT doesn't support MCP directly, but you can use Pro Worker AI via system prompt injection.

**Option A: Manual paste (simplest)**

1. Run the MCP server locally and call `proworker_get_calibration` to get your calibration JSON
2. Open ChatGPT > Settings > Personalization > Custom Instructions
3. Paste the CLAUDE.md content (or a condensed version) into "How would you like ChatGPT to respond?"
4. Paste your profile summary into "What would you like ChatGPT to know about you?"

**Option B: Full system prompt (more powerful)**

1. Start the MCP server: `cd mcp-server && python -m src.server`
2. Use any MCP client to read `proworker://system-prompt/yourname`
3. This returns the complete system prompt (CLAUDE.md + your profile)
4. Paste it into ChatGPT's custom instructions or a GPT's system prompt

**Option C: Build a custom GPT**

Create a GPT with:
- **Instructions**: The content from `proworker://system-prompt/yourname`
- **Conversation starters**: "Help me with [task]", "Coach me on [skill]"
- The GPT will behave according to your Pro Worker AI profile

---

### 5. Claude API (Programmatic)

For building applications that use Pro Worker AI programmatically.

**Direct API integration:**

```python
import anthropic
from pathlib import Path

# Load the system prompt
claude_md = Path("pro-worker-ai/CLAUDE.md").read_text()
profile = Path("pro-worker-ai/profiles/pro-yourname.md").read_text()
system_prompt = f"{claude_md}\n\n---\n\n# Active User Profile\n\n{profile}"

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system=system_prompt,
    messages=[{"role": "user", "content": "Help me write an evaluation framework"}]
)
```

**With MCP client library:**

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["-m", "src.server"],
    cwd="/path/to/pro-worker-ai/mcp-server",
    env={"PROWORKER_PROFILES_DIR": "/path/to/pro-worker-ai/profiles"}
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # Get profile
        profile = await session.call_tool("proworker_get_profile", {"name": "Angelo"})

        # Classify a task
        classification = await session.call_tool("proworker_classify_task", {
            "name": "Angelo",
            "task_description": "Write an economic analysis"
        })

        # Log interaction
        await session.call_tool("proworker_log_interaction", {
            "name": "Angelo",
            "task_category": "coach",
            "domain": "economic_analysis",
            "engagement_level": "active",
            "skill_signal": "growth"
        })
```

---

### 6. Custom Agents (Agent SDK, LangChain, CrewAI, etc.)

For building custom AI agents that respect Pro Worker AI.

**Pattern: Pre-action classification**

```python
# Before any agent action, classify the task
async def pro_worker_middleware(task, user_name, mcp_session):
    """Middleware that applies Pro Worker AI behavior to any agent."""

    result = await mcp_session.call_tool("proworker_classify_task", {
        "name": user_name,
        "task_description": task
    })
    classification = result.content[0].text

    if "protect" in classification:
        # Ask for hypothesis first
        return {
            "action": "ask_hypothesis",
            "prompt": "Before I help with this, what's your initial thinking?"
        }
    elif "coach" in classification:
        # Scaffold, don't solve
        return {
            "action": "scaffold",
            "prompt": "Let me help you think through this. What framework are you considering?"
        }
    elif "hands_off" in classification:
        # Surface decision, don't make it
        return {
            "action": "surface",
            "prompt": "This is a decision that needs your judgment. Here are the considerations..."
        }
    elif "automate" in classification:
        return {"action": "execute", "annotate": True}
    else:  # augment
        return {"action": "execute", "challenge": True}
```

**Pattern: Post-interaction logging**

```python
async def log_interaction(mcp_session, user_name, task_category, domain, engagement, signal):
    """Log every substantive interaction for skill tracking."""
    await mcp_session.call_tool("proworker_log_interaction", {
        "name": user_name,
        "task_category": task_category,
        "domain": domain,
        "engagement_level": engagement,
        "skill_signal": signal,
    })
```

**Pattern: Onboarding flow in any agent**

```python
async def run_onboarding(mcp_session, llm_client):
    """Run the Pro Worker AI onboarding assessment via MCP."""

    # 1. Get the assessment protocol
    protocol = await mcp_session.call_tool("proworker_assess_start", {})
    # protocol contains all questions and instructions

    # 2. Your agent/chatbot asks questions based on the protocol
    # ... (collect answers from user) ...

    # 3. Compute scores
    scores = await mcp_session.call_tool("proworker_assess_score", {
        "answers": collected_answers,
        "domain_ratings": domain_ratings
    })

    # 4. Create and save the profile
    result = await mcp_session.call_tool("proworker_assess_create_profile", {
        "name": user_name,
        "role": role,
        "organization": org,
        "industry": industry,
        "answers": collected_answers,
        "domain_ratings": domain_ratings,
        "career_goals": goals,
        # ... etc
    })
    # Profile is now saved and ready to use
```

---

### 7. OpenAI API / Other LLM APIs

For non-Anthropic LLMs, use the system prompt injection approach:

```python
import openai

# Load the Pro Worker AI system prompt
system_prompt = open("pro-worker-ai/CLAUDE.md").read()
profile = open("pro-worker-ai/profiles/pro-yourname.md").read()
full_prompt = f"{system_prompt}\n\n---\n\n# Active User Profile\n\n{profile}"

client = openai.OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": full_prompt},
        {"role": "user", "content": "Help me design a stakeholder engagement strategy"}
    ]
)
```

The system prompt works with any LLM that supports system instructions. The behavioral guidelines (cognitive forcing, contrastive explanations, task classification) are model-agnostic.

---

## Organizational Deployment

### For Teams / Companies

1. **Set up a shared profiles directory** (network drive, S3 bucket, Git repo)
2. **Run onboarding** for each team member via MCP assessment
3. **Connect the MCP server** to your team's tools
4. **Use the Streamlit dashboard** (`dashboard/app.py`) for org-level monitoring
5. **Re-assess** every 6 months (full) or 2 months (quick ADR check)

### Deployment options:

| Method | Complexity | Best for |
|--------|-----------|----------|
| Git repo + local MCP | Low | Individual / small team |
| Shared network profiles + per-machine MCP | Medium | Office teams |
| Central MCP server (HTTP transport) | High | Enterprise deployment |
| API wrapper service | High | SaaS product |

---

## MCP Server Reference

### Tools (13 total)

| Tool | Input | Output |
|------|-------|--------|
| `proworker_assess_start` | `{name?}` | Full assessment protocol (questions + instructions) |
| `proworker_assess_score` | `{answers, domain_ratings}` | Computed scores (ADR, GP, ALI, ESA, PWRI) |
| `proworker_assess_create_profile` | `{name, role, org, ...}` | Generated profile saved to disk |
| `proworker_get_profile` | `{name}` | Full profile markdown |
| `proworker_get_calibration` | `{name}` | Compact calibration JSON |
| `proworker_classify_task` | `{name, task_description}` | Task classification + recommended behavior |
| `proworker_log_interaction` | `{name, category, domain, ...}` | Logged interaction entry |
| `proworker_get_progression` | `{name}` | Skill progression stats + trends |
| `proworker_status` | `{name}` | Comprehensive status report |
| `proworker_org_summary` | `{}` | Org-level aggregation |
| `proworker_list_profiles` | `{}` | List of all profile names |
| `proworker_save_profile` | `{name, content}` | Save raw profile markdown |
| `proworker_delete_profile` | `{name}` | Delete profile + logs |

### Resources

| URI | Content |
|-----|---------|
| `proworker://profile/{name}` | Full profile markdown |
| `proworker://system-prompt/{name}` | CLAUDE.md + profile (ready for any LLM) |
| `proworker://coaching-modules` | Structured coaching sessions |
| `proworker://framework` | Assessment framework |
| `proworker://literature` | Research literature backing |

### Prompts

| Prompt | Description |
|--------|-------------|
| `proworker-system` | Full system prompt for any LLM |
| `proworker-assess` | Onboarding assessment (chatbot-driven) |
| `proworker-coach` | Coaching session (with optional focus domain) |
