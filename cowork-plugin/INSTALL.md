# Install TAOS in Claude Cowork

Talent-Augmenting OS turns Claude Cowork into a personalised coach: it assesses
your expertise, scaffolds your growth areas, challenges your expert areas, and
protects skills you don't want to lose to over-reliance on AI.

No hooks to configure, nothing to paste. Install the bundle, sign in once, and
say "run my TAOS assessment".

## What you need

- A Claude account with Cowork access (Pro, Max, Team, or Enterprise).
- A Google account — TAOS uses Google sign-in, same as the hosted web app.

## Step 1 — Get the bundle

Clone the repository and use the `cowork-plugin/` directory:

```sh
git clone https://github.com/angelo-leone/talent-augmenting-layer.git
```

The plugin is the `talent-augmenting-layer/cowork-plugin/` folder. Everything
Cowork needs is inside it.

## Step 2 — Add the plugin to Cowork

In Cowork, open **Customize → Plugins**, go to the **Personal** tab, and add the
`cowork-plugin/` folder as a local upload.

> Cowork's plugin install UI is still evolving. If the Personal/local-upload
> path is not where you expect it, see Anthropic's current guide:
> https://support.claude.com/en/articles/13837440-use-plugins-in-claude-cowork

## Step 3 — Connect the MCP server

The bundle's `.mcp.json` points Cowork at the TAOS server at
`https://proworker-hosted.onrender.com/mcp`. Cowork should pick this up when the
plugin is installed.

If it does not register automatically, add it by hand: **Customize → Connectors
→ Add custom connector**, name it `TAOS`, and paste the URL above.

Either way, the first time a TAOS skill calls a tool, Cowork walks you through
**Google sign-in**. Sign in. That links this Cowork session to your TAOS account,
so your profile is saved to your account and is available to every TAOS-aware
tool you use (Claude Code, the hosted web app, this).

You *can* skip sign-in and still run the assessment, but the profile will not be
tied to your account and will not persist. Signing in is strongly recommended.

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
- **Adjust calibration inline** — "push me harder on negotiation", "stop coaching
  me on SQL, I've got it", "never automate hiring decisions". Claude confirms the
  change and updates your profile.

## How this differs from Claude Code

If you also use the Claude Code plugin: there, coaching is ambient from turn one
because Claude Code runs a `SessionStart` hook. Cowork does not run plugin hooks,
so in Cowork you activate TAOS by invoking a skill — saying "assess me", "coach
me", or bringing a task. Once a skill is invoked, coaching stays active for the
whole conversation. In a new conversation, invoke a skill again.

## If a workspace folder is linked

If your Cowork project has a folder linked under "On your computer", TAOS will
also drop a copy of your profile at
`<workspace>/.talent-augmenting-layer/profiles/pro-<yourname>.md`. That local
copy is what the Claude Code plugin reads, so linking a folder keeps your
profile in sync across both tools. It is optional — your hosted account is the
source of truth.
