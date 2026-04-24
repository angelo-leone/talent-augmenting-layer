---
name: talent-sync
description: Push a local TAL profile (profiles/pro-*.md or ~/.talent-augmenting-layer/profiles/) up to the hosted web app at proworker-hosted.onrender.com so it can be viewed in the dashboard and used by the hosted remote-MCP endpoint. Use when a user wants their local profile to show up in the hosted UI.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Bash
---

# /talent-sync

Upload the local Talent-Augmenting Layer profile to the hosted web app so the user can view it in the dashboard and so the remote MCP endpoint can serve it.

## First: greet the user before any tool calls

> "Hi — I'll push your local TAL profile up to the hosted app so it shows up in your dashboard. One moment."

## Flow

1. Find the local profile. Check in order: `profiles/pro-*.md`, `profiles/tal-*.md`, `~/.talent-augmenting-layer/profiles/pro-*.md`, `~/.talent-augmenting-layer/profiles/tal-*.md`. If multiple, ask the user which one. If none, say: "I couldn't find a local profile. Run `/talent-augmenting-layer:talent-assess` first, then come back." and stop.
2. Read the profile markdown.
3. Check for a cached token at `~/.talent-augmenting-layer/auth.json`. The file should look like:
   ```json
   {"token": "eyJ...", "base_url": "https://proworker-hosted.onrender.com"}
   ```
4. If the file doesn't exist, or the token is obviously expired (older than 72 hours by mtime), prompt:
   > "I need an access token to sync. Please:
   > 1. Open **https://proworker-hosted.onrender.com/cli-token** in a browser.
   > 2. Sign in with Google if prompted.
   > 3. Copy the token shown on the page.
   > 4. Paste it here.
   >
   > The token is a session JWT valid for 72 hours. I'll cache it at `~/.talent-augmenting-layer/auth.json` for reuse."
   Wait for the user to paste the token. Trim whitespace. Write `~/.talent-augmenting-layer/auth.json` with the token and base_url.
5. POST the profile to `{base_url}/api/profile/sync` via `curl`:
   ```bash
   curl -sS -X POST "$BASE_URL/api/profile/sync" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d @<(jq -nc --rawfile content "$PROFILE_PATH" '{content_md: $content, scores_json: "{}"}')
   ```
   If `jq` is not installed, fall back to inline JSON:
   ```bash
   python3 -c 'import json, sys; print(json.dumps({"content_md": open(sys.argv[1]).read(), "scores_json": "{}"}))' "$PROFILE_PATH" \
     | curl -sS -X POST "$BASE_URL/api/profile/sync" \
         -H "Authorization: Bearer $TOKEN" \
         -H "Content-Type: application/json" \
         --data-binary @-
   ```
6. Parse the response. On `{"version": N, "message": "..."}`, tell the user: "Synced. You're now on version N. View it at {base_url}/dashboard."
7. On `401 Unauthorized`, delete the cached token (`rm ~/.talent-augmenting-layer/auth.json`) and restart from step 4 once.
8. On any other error, show the HTTP status and response body, and stop.

## Environment overrides

- `TAL_HOSTED_URL` — override the default `https://proworker-hosted.onrender.com`.
- Pilot testers running against a local dev instance can set `TAL_HOSTED_URL=http://localhost:8000`.

## What this does NOT do

- **No deletion.** Each sync creates a new profile *version* on the server. Old versions stay intact.
- **No automatic scoring.** `scores_json` is sent as an empty object unless the profile markdown has a `## TALQ Scores` block the skill can parse into JSON. Add that later if needed.
- **No merge.** If the user edited the profile in the web UI after the last sync, this overwrites that version with the local copy. Warn them before syncing if they've used the web UI recently.

Keep it short. If sync succeeds in one round, just say "Synced to version N."
