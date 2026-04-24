---
name: talent-update
description: Quick profile update based on recent work. Captures role changes, skill growth/atrophy, and AI usage patterns. Takes 3-5 minutes. Use when a user wants to refresh their profile.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - mcp__plugin_talent-augmenting-layer_talent-augmenting-layer__talent_get_progression
  - mcp__plugin_talent-augmenting-layer_talent-augmenting-layer__talent_log_interaction
  - mcp__plugin_talent-augmenting-layer_talent-augmenting-layer__talent_save_profile
  - mcp__plugin_talent-augmenting-layer_talent-augmenting-layer__talent_get_profile
---

# /talent-update

Run a quick TAL profile update. Profile is read/written locally. MCP tools used for logging when available.

## First: greet the user before any tool calls

Before calling any tool, send a short greeting:

> "Hi — I'll pull up your profile and run a quick 3–5 minute update. One moment."

Never go silent during setup.

## Flow

1. Find the user's profile via Glob on `profiles/pro-*.md` or `profiles/tal-*.md` in the current directory. Read it. If none exists, suggest `/talent-augmenting-layer:talent-assess` first and stop.
2. Check `profiles/log-{name}.jsonl` for recent interaction data (if present). If MCP is available, also call `talent_get_progression` for trend analysis — best-effort; don't block if the server is slow.
3. Ask a short update (3-5 questions max — see below).
4. Edit the local profile file directly and add a change log entry dated today.
5. If MCP tools are available, call `talent_log_interaction` to record this update session — best-effort.

## Update questions (3-5 max)

- Biggest challenge or win since last update?
- Any role changes, new responsibilities, or new tools?
- How has your AI usage changed? More dependent? More independent?
- Any skills you feel are growing or atrophying?
- Anything in the profile that no longer feels accurate?

Keep it brief and specific. Don't re-run the full assessment — just capture what's changed.
