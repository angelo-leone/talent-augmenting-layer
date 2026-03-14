# Talent-Augmenting Layer — Quick Start Guide

> Get Talent-Augmenting Layer running on any LLM platform in under 5 minutes.

---

## Step 1: Take the Assessment

Before using Talent-Augmenting Layer, you need a **profile**. Two options:

### Option A: Conversational Assessment (Recommended)
1. Open any LLM (ChatGPT, Claude, Gemini, etc.)
2. Paste the contents of `ASSESSMENT_PROMPT.md` into the system prompt or as your first message
3. The AI will guide you through a ~15 minute conversational assessment
4. At the end, you'll get a **profile markdown** — copy and save it

### Option B: Web Assessment
1. Open `web-ui/index.html` in your browser (no server needed)
2. Complete the ~10 minute form-based assessment
3. Download or copy the generated profile

### Option C: MCP Assessment (Claude Code / Cursor / Windsurf)
1. Set up the MCP server (see Tier 3 below)
2. Type `/talent-assess` or ask the AI to assess you
3. Profile is automatically saved to `profiles/pro-yourname.md`

---

## Step 2: Set Up Your Platform

### ChatGPT — Custom Instructions (Simplest)

1. Go to **Settings > Personalization > Custom instructions**
2. In **"What would you like ChatGPT to know about you?"** — paste your profile markdown
3. In **"How would you like ChatGPT to respond?"** — paste the contents of `SYSTEM_PROMPT_COMPACT.md`
4. Save. Every new conversation now uses Talent-Augmenting Layer.

> **Limitation**: ChatGPT custom instructions have a ~1,500 character limit per field. The compact prompt fits; for longer profiles, use a Custom GPT instead.

### ChatGPT — Custom GPT (Full Power)

1. Go to **Explore GPTs > Create a GPT**
2. In **Configure > Instructions** — paste the full contents of `SYSTEM_PROMPT.md`
3. In **Configure > Knowledge** — upload your profile `.md` file
4. Set **Conversation starters**:
   - "Help me with a task"
   - "Coach me on [skill]"
   - "Update my profile"
   - "Assess me (create new profile)"
5. Name it "Talent-Augmenting Layer" and save
6. Use this GPT for all your work conversations

### Google Gemini — Gem

1. Go to **gemini.google.com > Gems** (requires Gemini Advanced)
2. Click **Create a Gem**
3. In the **Instructions** field — paste the full contents of `SYSTEM_PROMPT.md`
4. Below the instructions, paste your profile markdown (Gems support long instructions)
5. Name it "Talent-Augmenting Layer"
6. Save and use for your work conversations

### Claude — Project (Recommended)

1. Go to **claude.ai > Projects** (requires Claude Pro)
2. Create a new project
3. In **Project Instructions** — paste the full contents of `SYSTEM_PROMPT.md`
4. In **Project Knowledge** — upload your profile `.md` file
5. Every conversation in this project uses Talent-Augmenting Layer

### Claude — Web (No Project)

1. Start a new conversation
2. Paste at the top of your first message:
```
[System context — please follow these instructions for this conversation]

[paste SYSTEM_PROMPT_COMPACT.md here]

[My profile:]
[paste your profile here]

---

Now, here's what I need help with: [your actual request]
```

### Claude Code / Cursor / Windsurf (Full MCP Integration)

See [Tier 3: MCP Server Setup](#tier-3-mcp-server) below.

### Any Other LLM (API or Chat)

1. If the LLM supports **system prompts** — paste `SYSTEM_PROMPT.md` as the system message, paste your profile after it
2. If the LLM only has **one text box** — paste `SYSTEM_PROMPT_COMPACT.md` + your profile at the start
3. The behavioural rules are model-agnostic and work with any capable LLM

---

## Step 3: Keep Your Profile Updated

Your profile should evolve as you grow. Three ways to update:

### Automatic (During Conversations)
Talent-Augmenting Layer will output a `PROFILE UPDATE BLOCK` at the end of substantive sessions when it observes skill changes. When you see this block:
1. Copy the changes
2. Update your profile in custom instructions / project settings
3. The updated profile takes effect in your next conversation

### Manual Check-In (Every 2-4 Weeks)
Tell your AI: "Let's update my profile." It will ask about:
- New skills or responsibilities
- Changes in how you use AI
- Progress on growth goals
- Any skills that feel rustier

### Hosted App (Full Automation)
If you use the hosted web app at [your-deployment-url]:
- Your profile is stored and versioned automatically
- You'll receive email reminders every 2 weeks for check-in questions
- Export your latest profile for any platform with one click

---

## Tier 3: MCP Server Setup

For Claude Code, Cursor, Windsurf, or any MCP-compatible editor.

### Install

```bash
cd talent-augmenting-layer/mcp-server
pip install -e .
```

### Configure

Add to your MCP settings (e.g., `.claude/settings.json`, `.cursor/mcp.json`):

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

### Use

- `/talent-assess` — Run the full assessment
- `/talent-coach` — Start a coaching session
- `/talent-update` — Update your profile
- The AI auto-loads your profile, classifies tasks, logs interactions, and tracks skill progression

---

## Tier 4: Hosted Web App

For organisations or individuals who want persistent profiles, automated reminders, and a dashboard.

### Features
- **LLM-powered conversational assessment** (not a form — a real conversation)
- **Google login** — your profile persists across sessions
- **2-week email reminders** — check-in questions to keep your profile current
- **Profile export** — one-click export for ChatGPT, Claude, Gemini
- **Personal dashboard** — track your growth over time

### Setup
See `hosted/README.md` for deployment instructions.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Tier 4: Hosted Web App                                     │
│  (LLM assessment, persistent profiles, email reminders)     │
├─────────────────────────────────────────────────────────────┤
│  Tier 3: MCP Server                                         │
│  (14 tools: assessment, profiles, tracking, coaching)       │
├─────────────────────────────────────────────────────────────┤
│  Tier 2: Platform-Native                                    │
│  (Custom GPTs, Gemini Gems, Claude Projects)                │
├─────────────────────────────────────────────────────────────┤
│  Tier 1: Universal System Prompt                            │
│  (Any LLM, copy-paste, zero infrastructure)                 │
└─────────────────────────────────────────────────────────────┘

All tiers share:
  ✓ Same TALQ assessment (14 fixed items + adaptive domains)
  ✓ Same scoring formulas (ADR, GP, ALI, ESA, TALRI)
  ✓ Same profile format (9 sections, portable markdown)
  ✓ Same behavioural rules (4 modes, de-skilling detection, task triage)
```

---

*Talent-Augmenting Layer v0.2.0 — CC BY-NC-SA 4.0 — github.com/angelo-leone/worker-augmenting-layer*
