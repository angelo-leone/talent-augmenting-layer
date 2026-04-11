---
name: talent-update
description: Quick profile update based on recent work. Captures role changes, skill growth/atrophy, and AI usage patterns. Takes 3-5 minutes. Use when a user wants to refresh their profile.
allowed-tools: [Read, Write, Glob, Grep, Bash]
---

# /talent-update

Run a Talent-Augmenting Layer profile update. Profile is always read/written locally. MCP tools used for logging when available.

## Flow

1. Find the user's profile in `profiles/pro-*.md` or `profiles/tal-*.md`. Read it directly from the local file.
2. Check `profiles/log-{name}.jsonl` for recent interaction data. If MCP is available, also call `talent_get_progression` for trend analysis.
3. Ask a short update (3-5 questions max — see below).
4. Edit the local profile file directly and add a change log entry.
5. If MCP tools are available, call `talent_log_interaction` to record this update session.

## Update questions (3-5 max)

- Biggest challenge or win since last update?
- Any role changes, new responsibilities, or new tools?
- How has your AI usage changed? More dependent? More independent?
- Any skills you feel are growing or atrophying?
- Anything in the profile that no longer feels accurate?

Keep it brief and specific. Don't re-run the full assessment — just capture what's changed.
