---
name: talent-pull
description: Download the user's TAL profile from the hosted web app (proworker-hosted.onrender.com) and cache it locally at ~/.talent-augmenting-layer/profiles/ so the SessionStart hook can read it on next session start. Use when the user created their profile via the remote MCP or hosted web assessment and wants ambient coaching to pick it up locally.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# /talent-pull

Fetch the user's profile from the hosted web app and drop it into the local cache that the TAL `SessionStart` hook scans on every new session.

## Why this exists

Plugin-install users create their profile on the hosted side (via the web assessment or the remote MCP). Their profile lives in Postgres at `proworker-hosted.onrender.com`. But the SessionStart hook in `plugin/hooks/inject-tal-layer.py` only checks local filesystem paths. Without `/talent-pull`, ambient coaching falls through to "no profile found" every session.

After running `/talent-pull` once, the profile is cached locally and the hook finds it on all subsequent sessions. Re-run any time you updated the profile on the hosted side and want the local cache refreshed.

## First: greet the user before any tool calls

> "Hi — I'll pull your hosted TAL profile down into the local cache so the ambient coach picks it up from turn one. One moment."

## Flow

1. Read the cached token at `~/.talent-augmenting-layer/auth.json`. Expected shape:
   ```json
   {"token": "eyJ...", "base_url": "https://proworker-hosted.onrender.com"}
   ```
2. If the file is missing or the token has expired (> 72 hours old by mtime), prompt the user:
   > "I need an access token. Open **https://proworker-hosted.onrender.com/cli-token** in a browser, sign in with Google, copy the token, and paste it here."
   Wait for the paste, trim whitespace, write `~/.talent-augmenting-layer/auth.json`.
3. GET `{base_url}/api/profile` with `Authorization: Bearer {token}`:
   ```bash
   curl -sS "$BASE_URL/api/profile" -H "Authorization: Bearer $TOKEN"
   ```
4. Parse the JSON. Expected keys: `version`, `created_at`, `scores`, `content_md`.
   - On `404`: "No profile on the hosted side. Run `/talent-augmenting-layer:talent-assess` first (either locally or at {base_url}/assess), then try again."
   - On `401`: delete the cached token and restart from step 2 once.
5. Extract a filename-safe name. Preferred source: parse `Name` from the profile's Identity Card section (line matching `| **Name** | <value> |`). Fallback: use the authenticated user's email from the `/api/auth/token` endpoint. Lowercase, kebab-case, e.g. `pro-angelo.md`.
6. Ensure `~/.talent-augmenting-layer/profiles/` exists (`mkdir -p`).
7. Write `content_md` to `~/.talent-augmenting-layer/profiles/pro-{name}.md`. Overwrite if present.
8. Report: "Pulled profile version N (hosted-created {created_at}) to `~/.talent-augmenting-layer/profiles/pro-{name}.md`. Ambient coaching will pick it up on next session."

## Environment overrides

- `TAL_HOSTED_URL` — default `https://proworker-hosted.onrender.com`. Pilot testers can point at a local dev server with `TAL_HOSTED_URL=http://localhost:8000`.

## Relationship to /talent-sync

- **`/talent-sync`** pushes the local profile UP to the hosted DB (local is source of truth).
- **`/talent-pull`** pulls the hosted profile DOWN to the local cache (hosted is source of truth).

Run whichever matches where the user is editing the profile. Running both on the same machine risks version drift; tell the user to pick one side as canonical for now.

Keep the report terse. If the pull succeeded in one round, just say "Pulled version N; run a fresh session to see ambient coaching pick it up."
