# Render service and database consolidation

You currently have two services and two databases on Render:

| Resource | Status | Action |
| --- | --- | --- |
| `proworker-hosted` (web service) | KEEP. You pay for it. The DNS `proworker-hosted.onrender.com` is the canonical URL referenced from `APP_URL`, system prompts, and the privacy policy. | Set the live `DATABASE_URL` env var to point at `proworker-db`. |
| `proworker-db` (PostgreSQL) | KEEP. You pay for it. Holds the live data. | Make this the only DB the live service connects to. |
| `talent-augmenting-layer-hosted` (web service) | LEGACY. Created during the rebrand. Not in active use. | Decommission once you have confirmed `proworker-hosted` is healthy. |
| `talent-augmenting-layer-db` (PostgreSQL) | LEGACY. | If it contains any data the production DB does not, dump and merge first. Otherwise decommission. |

`render.yaml` has been updated to match: the blueprint now references only `proworker-hosted` and `proworker-db`. The old names no longer appear.

---

## Step 1: authenticate the Render CLI on your machine

The CLI cannot run unattended. Either of these will work:

```bash
# Option A: interactive browser flow (one-time)
render login

# Option B: API key (set in your shell)
export RENDER_API_KEY="rnd_xxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Get an API key from Render dashboard → Account Settings → API Keys.

Verify:

```bash
render whoami
render workspaces
render workspace set    # if you have multiple workspaces
```

---

## Step 2: list resources and confirm what you want to keep

```bash
render services -o text
render services list -o text   # if your CLI version uses 'list'
```

Expected: you see four resources, the two `proworker-*` and the two `talent-augmenting-layer-*`. Note the resource IDs.

```bash
# Inspect the legacy DB to make sure it has nothing you need
render psql talent-augmenting-layer-db
\dt
SELECT (SELECT COUNT(*) FROM users) AS users,
       (SELECT COUNT(*) FROM profiles) AS profiles,
       (SELECT COUNT(*) FROM chat_logs) AS chat_logs;
\q
```

If the counts are all 0 (or you do not care about the data), proceed. If there is data you want to keep, dump it and load it into `proworker-db` first.

---

## Step 3 (optional, if there is data to migrate)

```bash
# Get connection strings
LEGACY_URL=$(render datastores info talent-augmenting-layer-db -o json | jq -r '.connectionInfo.externalConnectionString')
PROD_URL=$(render datastores info proworker-db -o json | jq -r '.connectionInfo.externalConnectionString')

# Dump and reload the public schema
pg_dump --no-owner --no-acl --schema=public "$LEGACY_URL" > /tmp/legacy-dump.sql
psql "$PROD_URL" < /tmp/legacy-dump.sql
```

Inspect for rows you actually want to keep before running the reload. If both DBs have rows for the same user, sort out conflicts manually first.

---

## Step 4: point the live service at `proworker-db` (if not already)

In the Render dashboard:

1. Open the `proworker-hosted` service.
2. Go to Environment.
3. Verify `DATABASE_URL` is set "From database: proworker-db". If it points at the legacy DB, change it.
4. Trigger a manual deploy.

Or via blueprint:

```bash
render blueprint launch    # applies render.yaml; will not destroy resources
```

---

## Step 5: decommission the legacy service and DB

This is irreversible. Confirm `proworker-hosted` is serving real traffic before you do this.

```bash
# Suspend first (safer than deleting; you can resume within 30 days)
render services suspend talent-augmenting-layer-hosted

# After a week of confirmed silence, delete:
render services delete talent-augmenting-layer-hosted

# Datastore: same pattern
render datastores delete talent-augmenting-layer-db
```

Render will prompt for `--confirm`; pass it explicitly or pipe `yes`.

---

## What I will not do without your input

1. I cannot run `render login` for you (interactive browser flow).
2. I cannot delete a paid resource for you. Even with an API key, I would surface a dry-run of the exact command and ask before executing the destructive step.
3. I cannot tell you which DB has the live data without connecting and inspecting both. The conservative default is "keep the one your service is currently pointed at".

When you are ready, set `RENDER_API_KEY` in your shell and tell me, and I will execute Steps 2 through 4 in this document. Step 5 (deletion) I will only execute after you re-confirm in that turn.
