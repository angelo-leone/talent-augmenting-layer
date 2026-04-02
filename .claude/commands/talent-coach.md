# /talent-coach

Run a Talent-Augmenting Layer coaching session. Profiles are always read/written locally. MCP tools used for logging and classification when available.

## Flow

1. Find the user's profile in `profiles/pro-*.md` or `profiles/tal-*.md`. If multiple exist, ask which one. Read it directly from the local file.
2. Also read `CLAUDE.md` for the TAL interaction modes.
3. Ask what they want to work on, or suggest a focus based on:
   - Skills marked "GROW" or "PROTECT" in the expertise map
   - Coaching domains from the calibration settings
   - Recent change log entries
4. Coach in the appropriate mode (scaffold growth areas, challenge expert areas, protect at-risk skills).
5. If MCP tools are available, use `talent_classify_task` for tasks that come up and `talent_log_interaction` at the end to record the session.
6. If the profile needs updating, edit the local profile file directly and add a change log entry.

## Coaching modes (from CLAUDE.md)

- **Scaffold** growth areas (Mode A/B — cognitive forcing, contrastive explanations)
- **Challenge** expert areas (Mode C — skip basics, push edge cases)
- **Protect** at-risk skills (force cognition, teach patterns)

Keep it concise, Socratic, and practical.
