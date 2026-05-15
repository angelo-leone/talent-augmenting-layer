# Install TAOS in Claude Cowork

Talent-Augmenting OS turns Claude Cowork into a personalised coach: it assesses
your expertise, scaffolds your growth areas, challenges your expert areas, and
protects skills you don't want to lose to over-reliance on AI.

No hooks to configure, nothing to paste. Add the marketplace, install the
**TAOS** plugin, sign in once, and say "run my TAOS assessment".

## What you need

- A Claude account with Cowork access (Pro, Max, Team, or Enterprise).
- A Google account — TAOS uses Google sign-in, same as the hosted web app.

## Step 1 — Add the marketplace

In Cowork:

1. Open **Customize**.
2. Click the **+** next to **Personal Plugins**.
3. Pick **Create plugin** → **Add marketplace**.
4. Paste the repository URL and click **Sync**:

```
https://github.com/angelo-leone/talent-augmenting-layer
```

Cowork reads the marketplace manifest at `.claude-plugin/marketplace.json` and
shows the plugins it lists.

## Step 2 — Install the TAOS plugin

Two plugins appear in the marketplace. Install **TAOS** (the one whose source
is `./cowork-plugin`).

> **Do not install "TAOS for Claude Code"** in Cowork. That variant assumes a
> SessionStart hook that Cowork does not run, so its skills are intentionally
> short and depend on context the hook injects. In Cowork its skills look
> shortened and underpowered. Stick to **TAOS** in any Cowork install.

If you already installed the wrong one earlier, uninstall it before adding the
new one.

## Step 3 — Sign in

The plugin's `.mcp.json` points Cowork at the TAOS server at
`https://proworker-hosted.onrender.com/mcp`. The first time a TAOS skill calls
a tool, Cowork walks you through **Google sign-in**. Sign in: that links this
Cowork session to your TAOS account, so your profile is saved server-side and
is available to every TAOS-aware tool you use (Claude Code, the hosted web
app, this).

You *can* skip sign-in and still run the assessment, but the profile will not
be tied to your account and will not persist. Signing in is strongly
recommended.

## Step 4 — Start

Just talk to Claude. Say:

```
Run my TAOS assessment
```

Claude picks up the `talent-assess` skill, which carries the full TAOS coaching
layer, and walks you through a ~15 minute conversational assessment. When it
finishes, your profile is saved and Claude is operating as your coach for the
rest of the conversation.

## After setup — things to try

- **"Coach me on \[skill\]"** — runs a targeted coaching session against your profile.
- **Bring a real work task** — Claude classifies it (automate / augment / coach /
  protect / hands-off) and calibrates how much it does for you vs. with you.
- **"Update my profile"** — a quick 3-5 minute refresh when your work changes.
- **"Speed mode"** — temporarily drop coaching for a single task. Every override
  is logged so frequent use in a coaching domain shows up next time you update.
- **Adjust calibration inline** — "push me harder on negotiation", "stop coaching
  me on SQL, I've got it", "never automate hiring decisions". Claude confirms
  the change and updates your profile.

## How this differs from Claude Code

If you also use the Claude Code plugin: there, coaching is ambient from turn
one because Claude Code runs a `SessionStart` hook. Cowork does not run plugin
hooks, so in Cowork you activate TAOS by invoking a skill — saying "assess me",
"coach me", "speed mode", or bringing a task. Once a skill is invoked, coaching
stays active for the whole conversation. In a new conversation, invoke a skill
again.

## If a workspace folder is linked

If your Cowork project has a folder linked under "On your computer", TAOS will
also drop a copy of your profile at
`<workspace>/.talent-augmenting-layer/profiles/pro-<yourname>.md`. That local
copy is what the Claude Code plugin reads, so linking a folder keeps your
profile in sync across both tools. It is optional — your hosted account is the
source of truth.
