# /talent-update

Run a Talent-Augmenting Layer profile update. No remote API or MCP server required — reads and writes profiles locally.

## How it works

1. Find the user's profile in `profiles/pro-*.md`. If multiple exist, ask which one.
2. Read the full profile to understand current state.
3. Ask a short update (3-5 questions max):
   - Biggest challenge or win since last update?
   - Any role changes, new responsibilities, or new tools?
   - How has your AI usage changed? More dependent? More independent?
   - Any skills you feel are growing or atrophying?
   - Anything in the profile that no longer feels accurate?
4. Based on the conversation, update the profile file:
   - Adjust expertise ratings if warranted (with evidence)
   - Update growth directions, goals, or task classifications
   - Modify calibration settings if dependency/growth signals changed
   - Update the "Last updated" date
5. Add a change log entry at the bottom of the profile with today's date, what changed, and the trigger ("talent-update").

Keep it brief and specific. Don't re-run the full assessment — just capture what's changed.
