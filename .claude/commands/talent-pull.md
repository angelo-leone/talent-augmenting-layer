# /talent-pull

Download the user's TAL profile from the hosted app and cache it locally so the SessionStart hook finds it.

## Why

Plugin users whose profile lives in the remote DB get "no profile found" from the ambient hook because the hook only checks local filesystem. `/talent-pull` mirrors the remote profile into `~/.talent-augmenting-layer/profiles/` once, and subsequent sessions load it automatically.

## First: greet the user before any tool calls

> "Hi — I'll pull your hosted TAL profile down into the local cache so the ambient coach picks it up from turn one. One moment."

## Flow

1. Read `~/.talent-augmenting-layer/auth.json` for the cached token (`{"token": "eyJ...", "base_url": "..."}`).
2. If missing or > 72 hours old, prompt:
   > "Open **https://proworker-hosted.onrender.com/cli-token** in a browser, sign in with Google, copy the token, and paste it here."
   Trim whitespace, write `~/.talent-augmenting-layer/auth.json`.
3. `curl -sS "$BASE_URL/api/profile" -H "Authorization: Bearer $TOKEN"` → expect JSON with `version`, `created_at`, `scores`, `content_md`.
   - 404 → "No profile on the hosted side. Run `/talent-augmenting-layer:talent-assess` first."
   - 401 → delete the cached token and retry step 2 once.
4. Pick a filename-safe name from the profile's `| **Name** | <value> |` row (fallback: authenticated user's email).
5. `mkdir -p ~/.talent-augmenting-layer/profiles/` and write `content_md` to `~/.talent-augmenting-layer/profiles/pro-{name}.md`.
6. Report: "Pulled version N; run a fresh session to see ambient coaching pick it up."

## Env overrides

- `TAL_HOSTED_URL` — default `https://proworker-hosted.onrender.com`.

## Related

- `/talent-sync` pushes local → hosted. `/talent-pull` pulls hosted → local. Pick one side as canonical.
