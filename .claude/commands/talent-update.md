# /talent-update

Run a Talent-Augmenting Layer profile update. Uses MCP tools when available, falls back to local files.

## Flow

### If the MCP server is connected (preferred)

1. Call `talent_get_profile` to load the current profile.
2. Call `talent_get_progression` to review recent interaction data and skill trends.
3. Ask a short update (3-5 questions max — see below).
4. Update the profile and save with `talent_save_profile`.
5. Call `talent_log_interaction` to record this update session.

### If no MCP server is connected (local fallback)

1. Find the user's profile in `profiles/pro-*.md` or `profiles/tal-*.md`.
2. Read the profile. Also check `profiles/log-{name}.jsonl` for recent interaction data.
3. Ask the update questions.
4. Edit the profile file directly and add a change log entry.
5. Append an interaction log entry to `profiles/log-{name}.jsonl`.

## Update questions (3-5 max)

- Biggest challenge or win since last update?
- Any role changes, new responsibilities, or new tools?
- How has your AI usage changed? More dependent? More independent?
- Any skills you feel are growing or atrophying?
- Anything in the profile that no longer feels accurate?

Keep it brief and specific. Don't re-run the full assessment — just capture what's changed.
