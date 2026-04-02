# Claude Code First-Time Setup Guide (Remote MCP)

This guide is for a brand new user who wants to:
- install Claude Code,
- connect the remote Talent-Augmenting Layer MCP server,
- and run /talent-assess, /talent-coach, and /talent-update.

This setup uses your Claude Code model session for the conversation. You do not need to configure Gemini/OpenAI/Anthropic API keys for MCP prompts/tools.

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

## 3. Add Remote MCP Server Config

Create or edit this file:

~/.claude/settings.json

Paste this JSON:

{
  "mcpServers": {
    "talent-augmenting-layer": {
      "url": "https://proworker-hosted.onrender.com/mcp/sse",
      "description": "Talent-Augmenting Layer -- Remote MCP Server"
    }
  }
}

Save the file, then fully restart Claude Code.

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

In Claude Code, check that the MCP server is available and then run:
- /talent-assess
- /talent-coach
- /talent-update

Expected behavior:
- The conversation is run by your selected Claude Code model.
- TAL tools/prompts/resources come from the remote MCP server.
- No hosted web-app LLM key is required for this MCP path.

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

For this setup, use MCP prompts/tools and slash commands in Claude Code.
That error usually appears when a web-app assessment path is used instead of MCP flow.
In MCP flow, your Claude Code model runs the conversation and no separate hosted LLM API key is needed.

## 8. What Lives Where

- Conversation model: your Claude Code model selection
- TAL tools/prompts/resources: remote MCP server
- Profile data: TAL server storage
- Slash command definitions: local command markdown files

## 9. Next Reference Docs

- docs/REMOTE_MCP_SETUP.md
- mcp-server/README.md
- docs/integration-guide.md
