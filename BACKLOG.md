# TAOS backlog

This is the live backlog for Talent-Augmenting OS (TAOS). It is repository-local and not part of any system prompt or production payload. Update freely. Most recent at top.

Last updated: 2026-04-30.

---

## Conventions

- **Blocked-on-me**: needs the user to provide creds, an account, an external decision, or a stakeholder input.
- **Code**: concrete code work; can be picked up in a future session with no external dependency.
- **Process**: not a code change; involves vendors, certifications, contracts, or schedules.
- **Smoke**: manual verification the user does to validate something already shipped.
- Each item has a one-line "next action" so it can be picked up cold.

---

## A. Blocked-on-me (waiting on user)

### A1. Render destructive consolidation
- Decommission `talent-augmenting-layer-hosted` and `talent-augmenting-layer-db`.
- Keep `proworker-hosted` and `proworker-db` (paid).
- `render.yaml` is already updated; the runbook is in `docs/RENDER_CONSOLIDATION.md`.
- **Next action**: user runs `render login` or sets `RENDER_API_KEY` in shell, then says "go"; I run steps 2 to 4 and ask before step 5 (deletion).

### A2. Rotate the leaked MCP registry token
- `.mcpregistry_registry_token` was visible in pre-`994e90c` commits on GitHub. Old smoke-test #1.
- **Next action**: user rotates at the MCP registry out of band; once rotated, I scrub the value from history with `git-filter-repo` if you want history-clean.

### A3. Pass 2 rebrand (breaking)
- Rename slash commands `talent-*` to `taos-*`, MCP tool names `talent_*` to `taos_*`, plugin slug `talent-augmenting-layer` to `talent-augmenting-os`, GitHub repo, local directory.
- The 10 Vanguard pilot users will need to re-install. Solita has not yet started.
- **Next action**: user says "Pass 2 now" once Vanguard pilot has been notified; I run a coordinated rename script with `taos_` prefix.

### A4. Solita pilot security questionnaire
- They will hand you their security questionnaire (SIG, CAIQ, or custom). The answers will reshape priorities below.
- **Next action**: user obtains the questionnaire from Solita; I draft answers using `LICENSE`, `COMMERCIAL.md`, `PRIVACY_POLICY.md`, and the security posture in `hosted/security.py`.

### A5. EU data residency provisioning
- `PRIVACY_POLICY.md` promises an EU residency option. We have not provisioned a Frankfurt Render instance.
- **Next action**: user confirms whether Solita actually requires EU residency. If yes, ~half a day to deploy a parallel Frankfurt service and swap DNS / per-customer routing.

---

## B. Code (no blockers)

### B1. Per-route rate limits
- `hosted/security.py` exposes `LIMIT_LOGIN`, `LIMIT_ASSESS`, `LIMIT_API`, `LIMIT_MCP` constants; helpers are not yet attached to handlers.
- **Next action**: add `@limiter.limit(LIMIT_LOGIN)` to `/login` and `/auth/callback`, `LIMIT_ASSESS` to `/api/assess/message`, `LIMIT_API` to all `/api/*`, `LIMIT_MCP` to the MCP transports.

### B2. Full audit-log coverage
- `hosted/audit_log.py` documents the full action vocabulary; only 5 actions are wired (admin.dashboard_viewed, org.invite_sent, org.invite_revoked, account.exported, account.deleted).
- **Next action**: wire `record(...)` into `auth.login`, `auth.logout`, `auth.session_revoked`, `org.invite_accepted`, `org.member_role_changed`, `profile.created`, `profile.updated`, `profile.deleted`, `profile.exported`, `oauth.token_issued`, `oauth.token_revoked`. Half a day.

### B3. SSO scaffold via WorkOS
- Solita will almost certainly require SAML or OIDC SSO at scale. Google OAuth alone will not pass.
- **Next action**: pick WorkOS over Auth0 or Stytch (single integration covers SAML + OIDC + SCIM). Add `hosted/sso.py`, swap `setup_oauth` for the WorkOS authkit when `SSO_PROVIDER=workos`. Half a day to scaffold; ~1-2 days to wire to a real IdP once Solita gives access.

### B4. Live test pass
- I have not run the dev server end-to-end since the palette swap, security middleware, audit log, GDPR endpoints, and rate limiter were added.
- **Next action**: `pip install -r hosted/requirements.txt && uvicorn hosted.app:app --reload` locally, click through landing, demo, login, dashboard, admin, /admin/audit, /api/account/export. Note any CSP violations in the browser console. Adjust `_CSP_DIRECTIVES` if anything legitimate is blocked.

### B5. Compass SVG and stragglers from palette swap
- `hosted/static/compass.svg`, `web-ui/index.html`, `hosted/templates/assessment.html` may still carry the old red/dark hex codes.
- **Next action**: `grep -rn "#e94560\|#1a1a2e\|#16213e\|#533483" .` and replace with the new tokens. Quick.

### B6. Pre-commit hook to block `pilot/` re-entry
- Belt-and-braces against the gitignore being weakened.
- **Next action**: add `.git/hooks/pre-commit` (or a husky-style cross-machine hook in `.githooks/`) that exits non-zero if any staged path matches `^pilot/`.

### B7. CSV-based bulk member invite
- Invite UI is one-at-a-time. A 2,500-person pilot does not invite one user at a time.
- **Next action**: add `POST /api/admin/invite/bulk` accepting CSV (email, role); reuse the existing single-invite path in a loop with rate limiting.

### B8. Audit log retention purge
- Rows are append-only; nothing currently removes old rows. SOC 2 wants documented retention.
- **Next action**: add a daily APScheduler job in `hosted/scheduler.py` that deletes `AuditLog` rows older than `AUDIT_RETENTION_DAYS` (default 365). Tiny.

### B9. /admin/audit pagination + filters
- Currently shows the most recent 200; no filter by action, actor, or date range.
- **Next action**: add `?from=...&to=...&action=...&actor_email=...` query params and a small filter form.

### B10. Restore-test the Render Postgres backups
- We have backups (Render-managed) but never tried restoring.
- **Next action**: spin up a temporary Render Postgres, restore the latest backup, run the schema sanity SQL, tear it down. Document the runbook.

### B11. Custom 404 / 500 / 429 pages
- FastAPI shows the default white error page; in branded UI this looks broken.
- **Next action**: add three template handlers tied to `RequestValidationError`, `HTTPException`, and `RateLimitExceeded`.

### B12. Account-deletion confirmation UX
- `DELETE /api/account` is live but no UI surfaces it. Privacy policy promises subject access.
- **Next action**: add a "Delete my account" button on the dashboard with a typed-confirmation modal (user types their email to confirm).

---

## C. Process (vendors, contracts, time)

### C1. Move off Render free tier on the live service
- Free tier sleeps after ~15 minutes idle; pilot users will hit cold starts.
- **Next action**: upgrade `proworker-hosted` to Render Starter ($7/mo at time of writing); `render.yaml` already specifies `plan: starter` so the next blueprint apply will do it.

### C2. Status page
- Procurement teams expect a status URL.
- **Next action**: pick Better Stack, statuspage.io, or instatus. Wire a single component for `proworker-hosted`. ~1 hour.

### C3. SOC 2 Type II readiness programme
- Standard ask for US enterprise pilots. ~3 months to Type I + ~6 months observation window for Type II.
- **Next action**: pick Drata, Vanta, or Secureframe. Run their evidence-collection bot against the repo and Render. Cost rough range $20-60k year one (confidence: medium, varies a lot).

### C4. ISO 27001 (alternative for EU pilots)
- Often substitutable for SOC 2 with EU customers.
- **Next action**: only pursue if Solita or a future EU customer specifically asks; otherwise SOC 2 covers the same ground in their eyes.

### C5. External penetration test
- Recommended firms for AI-aware testing: Cure53, Trail of Bits, Cobalt.
- **Next action**: schedule a one-week test before the first paying customer goes live. Budget rough range $15-40k (confidence: low; scope dependent).

### C6. Cyber liability insurance
- Standard ask in enterprise procurement.
- **Next action**: get a quote from Coalition or At-Bay before the first paid contract.

### C7. DPA template
- We will need a signed Data Processing Agreement when the first EU customer signs.
- **Next action**: use a vetted template (Iubenda, TermsFeed, or your law firm). Have it ready before negotiation, not during.

### C8. Trademark check on "Talent-Augmenting OS" / "TAOS"
- Before the rebrand goes external on marketing, check that "TAOS" is not held in a relevant class.
- **Next action**: USPTO TESS search and EUIPO search; if clear, file an application in classes 9 and 42.

---

## D. Smoke tests (manual verification by user)

These were in the previous Project Status; carrying forward whatever you have not yet done.

### D1. Promote yourself to org owner via SQL
```sql
INSERT INTO organizations (name, slug) VALUES ('Vanguard', 'vanguard');
UPDATE users SET org_id = 1, role = 'owner' WHERE email = 'angelo.leone1204@gmail.com';
```
Run against `proworker-db`.

### D2. Test the invite flow end-to-end
Sign in to `/admin`, invite a throwaway email you control, open the link in incognito, accept, verify user lands on `invite_accepted.html` with correct `org_id` and role.

### D3. Trigger the unknown-task protocol
Ask the agent something fully outside your profile (e.g. "help me diagnose a Kubernetes pod failing health checks"). Confirm it asks the "automate now or get better long-term?" question, then updates the profile with the new domain + dated change-log entry before executing.

### D4. Exercise `/talent-sync` and `/talent-pull`
From `/Users/angelo.leone/Documents/try-tal`, verify the JWT to `~/.talent-augmenting-layer/auth.json` handshake works, and a pulled profile lands in `~/.talent-augmenting-layer/profiles/pro-*.md` for the next session's hook to pick up.

### D5. Verify Codex CLI config shape
Check `~/.codex/config.json` vs `config.toml` against the current Codex docs before pointing pilot users at it.

### D6. Retrieve Stan's `session_id`
Email Stan or query the DB so we can inspect his `conversation_json` against `latency_ms` fields and confirm the 20-minute stall pattern is visible in data.

### D7. Warm-wake the live app before pilot demo
`curl https://proworker-hosted.onrender.com/` (or open in browser) before sending any pilot user the link; the free tier sleeps after ~15 minutes of inactivity. Becomes obsolete once C1 lands.

### D8. Verify the new landing page, demo, and design (this push)
Open `https://proworker-hosted.onrender.com/`, then `/demo`. Confirm: white background, sage green accents, no red, the demo runs both Phase 1 (assessment) and Phase 2 (coach), and the coach phase shows the yellow caveat banner. Render auto-deploys from `main`; allow a few minutes after the push.

---

## How to use this file

When picking up a TAOS session cold, read this file first. Pick an item with no blockers; do it; tick it off here in the same commit. If you discover a new gap during work, add it before you forget. If a blocked-on-me item gets unblocked, move it from A to B and start it.

If a task touches the live deployment, run the smoke tests in D before declaring it done.
