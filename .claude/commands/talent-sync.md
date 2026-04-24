# /talent-sync

Push the local TAL profile to the hosted web app at proworker-hosted.onrender.com.

## First: greet the user before any tool calls

> "Hi — I'll push your local TAL profile up to the hosted app so it shows up in your dashboard. One moment."

## Flow

1. Glob for the profile: `profiles/pro-*.md`, `profiles/tal-*.md`, `~/.talent-augmenting-layer/profiles/pro-*.md`, `~/.talent-augmenting-layer/profiles/tal-*.md`. If multiple, ask which. If none, tell the user to run `/talent-augmenting-layer:talent-assess` first and stop.
2. Read the profile markdown.
3. Check for a cached token at `~/.talent-augmenting-layer/auth.json` (format: `{"token": "eyJ...", "base_url": "..."}`).
4. If missing or the file mtime is > 72 hours, prompt:
   > "Open **https://proworker-hosted.onrender.com/cli-token** in a browser, sign in with Google, copy the token shown, and paste it here."
   Wait for the paste. Trim whitespace. Write `~/.talent-augmenting-layer/auth.json`.
5. POST to `{base_url}/api/profile/sync`:
   ```bash
   python3 -c 'import json, sys; print(json.dumps({"content_md": open(sys.argv[1]).read(), "scores_json": "{}"}))' "$PROFILE_PATH" \
     | curl -sS -X POST "$BASE_URL/api/profile/sync" \
         -H "Authorization: Bearer $TOKEN" \
         -H "Content-Type: application/json" \
         --data-binary @-
   ```
6. On `{"version": N}`: "Synced. You're on version N. View at {base_url}/dashboard."
7. On `401`: delete the cached token and retry step 4 once.
8. On any other error, show the HTTP status + response body and stop.

## Env overrides

- `TAL_HOSTED_URL` — default `https://proworker-hosted.onrender.com`.

## Not supported (yet)

- No merge with web-UI edits. Sync overwrites with the local copy.
- `scores_json` sent empty unless the profile has a parseable TALQ Scores block.
- No deletion — each sync creates a new profile version.
