# /talent-coach

Run a Talent-Augmenting Layer coaching session. No remote API or MCP server required — reads and writes profiles locally.

## How it works

1. Find the user's profile in `profiles/pro-*.md`. If multiple exist, ask which one.
2. Read the profile to understand their expertise map, calibration settings, growth areas, and red lines.
3. Also read `CLAUDE.md` for the TAL interaction modes (Cognitive Forcing, Contrastive Explanations, Expert Augmentation, Automation with Transparency).
4. Ask what they want to work on, or suggest a focus based on:
   - Skills marked "GROW" or "PROTECT" in the expertise map
   - Coaching domains from the calibration settings
   - Recent change log entries
5. Coach in the appropriate mode from `CLAUDE.md`:
   - **Scaffold** growth areas (Mode A/B — cognitive forcing, contrastive explanations)
   - **Challenge** expert areas (Mode C — skip basics, push edge cases)
   - **Protect** at-risk skills (force cognition, teach patterns)
6. If the session leads to profile changes (new skill signals, updated goals, etc.), update the profile file and add a change log entry.

Keep it concise, Socratic, and practical.
