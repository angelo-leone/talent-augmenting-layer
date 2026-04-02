# /talent-coach

Run a Talent-Augmenting Layer coaching session. Uses MCP tools when available, falls back to local files.

## Flow

### If the MCP server is connected (preferred)

1. Call `talent_get_profile` to load the user's profile.
2. Call `talent_get_calibration` to get current calibration settings.
3. Ask what they want to work on, or suggest a focus from the profile.
4. Coach in the appropriate mode (scaffold growth areas, challenge expert areas, protect at-risk skills).
5. Use `talent_classify_task` to classify tasks that come up.
6. At the end, call `talent_log_interaction` to record the session (domain, engagement level, skill signals).
7. If the profile needs updating, call `talent_save_profile`.

### If no MCP server is connected (local fallback)

1. Find the user's profile in `profiles/pro-*.md` or `profiles/tal-*.md`. If multiple exist, ask which one.
2. Read the profile + `CLAUDE.md` for TAL interaction modes.
3. Coach as above.
4. Append an interaction log entry to `profiles/log-{name}.jsonl` (JSON with fields: timestamp, task_category, domain, engagement_level, skill_signal, notes).
5. If the profile needs updating, edit the profile file directly and add a change log entry.

## Coaching modes (from CLAUDE.md)

- **Scaffold** growth areas (Mode A/B — cognitive forcing, contrastive explanations)
- **Challenge** expert areas (Mode C — skip basics, push edge cases)
- **Protect** at-risk skills (force cognition, teach patterns)

Keep it concise, Socratic, and practical.
