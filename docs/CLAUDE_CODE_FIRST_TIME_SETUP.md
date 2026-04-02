# Claude Code First-Time Setup Guide

This guide is for a brand new user who wants to:
- install Claude Code,
- connect the Talent-Augmenting Layer MCP server (local or remote),
- and run /talent-assess, /talent-coach, and /talent-update.

Your Claude Code model drives the conversation. The MCP server provides tools for scoring, profile management, interaction logging, and progression tracking. No Gemini/OpenAI/Anthropic API keys needed.

## 1. Prerequisites

You need:
- A Claude account with access to Claude Code
- Internet access
- A terminal on your machine

## 2. Install Claude Code

Use the official installer:

curl -fsSL https://claude.ai/install.sh | bash

Then make sure the Claude Code binary is on PATH.

If your shell is zsh:

echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

If your shell is bash:

echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

Verify install:

claude --version

If the command is not found, restart your terminal and run the PATH step again.

## 3. Connect the MCP Server

### Option A: Local MCP server (recommended)

Runs on your machine via stdio. No network dependency, no credential issues. Data stays in `profiles/`.

1. Clone this repo and install the MCP server dependencies:

```
cd talent-augmenting-layer/mcp-server
pip install -e .
```

2. Create or edit `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "talent-augmenting-layer": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/talent-augmenting-layer/mcp-server",
      "env": {
        "TALENT_AUGMENTING_LAYER_PROFILES_DIR": "/path/to/talent-augmenting-layer/profiles"
      }
    }
  }
}
```

Replace `/path/to/talent-augmenting-layer` with your actual repo path.

3. Restart Claude Code.

### Option B: Remote MCP server

Connects to the hosted server on Render. No local install needed, but requires the server to be running.

Create or edit `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "talent-augmenting-layer": {
      "url": "https://proworker-hosted.onrender.com/mcp/sse",
      "description": "Talent-Augmenting Layer — Remote MCP Server"
    }
  }
}
```

Restart Claude Code.

**Note**: If you get "Could not load credentials" errors from the remote server, switch to Option A (local). The remote server's hosted app dependency chain can trigger this — it's unrelated to MCP tool functionality.

## 4. Enable Slash Commands

MCP config connects tools/prompts, but slash commands are loaded from command files.

You have two options:

Option A (recommended):
- Open this repository in Claude Code.
- Claude Code loads the files in .claude/commands automatically.

Option B (global commands):
- Copy these files into your global commands folder ~/.claude/commands/:
  - .claude/commands/talent-assess.md
  - .claude/commands/talent-coach.md
  - .claude/commands/talent-update.md

## 5. Verify Everything Works

In Claude Code, check that the MCP server is connected, then run:
- /talent-assess
- /talent-coach
- /talent-update

Expected behavior:
- The conversation is driven by your Claude Code model.
- TAL tools (scoring, profile CRUD, interaction logging, progression tracking) come from the MCP server.
- Profiles and interaction logs are stored in `profiles/` (local server) or on the hosted server (remote).
- If the MCP server isn't connected, the commands fall back to reading/writing local files directly.

## 6. Recommended First Run

1. Run /talent-assess to create your initial profile.
2. Run /talent-coach for one focused coaching session.
3. Run /talent-update after a few interactions to evolve your profile.

## 7. Troubleshooting

### Claude command not found

- Confirm Claude Code is installed: claude --version
- Confirm PATH includes ~/.local/bin
- Restart terminal and Claude Code

### MCP tools do not appear

- Validate JSON in ~/.claude/settings.json
- Confirm URL is exactly https://proworker-hosted.onrender.com/mcp/sse
- Restart Claude Code completely

### Slash commands do not appear

- Confirm you opened this repo in Claude Code, or copied command files to ~/.claude/commands/
- Restart Claude Code

### Could not load credentials from any providers

This error comes from the remote hosted server's Google/Anthropic dependency chain — not from the MCP server itself.

**Fix**: Switch to the local MCP server (Step 3, Option A). The local server depends only on `mcp`, `pyyaml`, and `pymupdf` — no Google/Anthropic/OpenAI packages. All tools, logging, and progression tracking work identically.

## 8. What Lives Where

| Component | Location |
|-----------|----------|
| Conversation model | Your Claude Code model selection |
| TAL tools/prompts/resources | MCP server (local or remote) |
| Profile data (`.md`) | `profiles/` directory (local server) or hosted DB (remote) |
| Interaction logs (`.jsonl`) | `profiles/log-{name}.jsonl` (local server) or hosted DB (remote) |
| Slash command definitions | `.claude/commands/` in this repo or `~/.claude/commands/` |
| Scoring & assessment logic | `mcp-server/src/assessment.py` (used by MCP server and as local fallback) |

## 9. Next Reference Docs

- docs/REMOTE_MCP_SETUP.md
- mcp-server/README.md
- docs/integration-guide.md
