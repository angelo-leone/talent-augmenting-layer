# Remote MCP Access — Setup Guide

> **TL;DR**: Non-technical people can access the MCP server from anywhere by copying a single JSON config file. The MCP server is now available at `https://proworker-hosted.onrender.com/mcp/sse`.

## Overview

The Talent-Augmenting Layer MCP server is now accessible remotely via Server-Sent Events (SSE) over HTTP. This means:

✅ **No local installation needed** — just a configuration update   
✅ **Works from anywhere** — home, office, coffee shop, etc.   
✅ **Works with any IDE** — Claude Desktop, Cursor, VSCode, etc.   
✅ **No coding required** — copy-paste configuration  
✅ **Instant access** — profiles, assessments, coaching, system prompts all accessible

---

## Architecture

### Before (Local Only)
```
IDE (Claude Desktop/Cursor)
  ↓ (stdio)
MCP Server (local subprocess on your machine)
  ↓
TAL profiles & tools
```

### After (Remote + Local)
```
IDE (Claude Desktop/Cursor) anywhere
  ↓ (HTTP/SSE)
https://proworker-hosted.onrender.com/mcp/sse
  ↓
Hosted TAL MCP Server (on Render)
  ↓
Database + TAL profiles & tools (shared across all users)
```

---

## Setup Instructions

### Option 1: Remote Access (Recommended for Non-Technical People)

#### Step 1: Get Your Config File
Copy one of these configuration files based on your IDE:

**For Claude Desktop:**
- File: `mcp-server/claude-desktop-config-remote.json`
- Location to paste: `~/.config/Claude Desktop/claude_desktop_config.json`

**For Cursor:**
- File: `mcp-server/claude-code-config-remote.json`
- Location to paste: `~/.cursor/mcp_config.json` or `~/.config/Cursor/mcp_config.json`

**For VSCode (with MCP extension):**
- File: `mcp-server/claude-code-config-remote.json`
- Location to paste: `.vscode/settings.json` (under `mcp.servers` key)

#### Step 2: Paste Configuration
1. Open your IDE's configuration file (see locations above)
2. Replace the entire contents with the configuration from the file
3. Save and close the file
4. **Restart your IDE**

Important: this config only connects the client to the MCP server. It does not install Claude Code slash commands.

If you want the slash commands, open this repository in Claude Code so it can load `.claude/commands/`, or copy the files into your own `~/.claude/commands/` folder.

#### Step 3: Verify Connection
In your IDE, you should now see "talent-augmenting-layer" in your available MCP tools/resources.

Try running one of these commands:
- `@talent.profile <your-name>` — Load your profile
- `@talent.status <your-name>` — Get your status report
- `@talent.list-profiles` — See all available profiles

---

### Option 2: Local Access (For Advanced Users)

If you prefer to run the MCP server locally on your machine:

```bash
cd mcp-server
python -m src.server
```

Then use the local configuration files:
- `mcp-server/claude-desktop-config.json` (local)
- `mcp-server/claude-code-config.json` (local)

---

## Remote Configuration File

**File**: `mcp-server/claude-desktop-config-remote.json`

```json
{
  "mcpServers": {
    "talent-augmenting-layer": {
      "url": "https://proworker-hosted.onrender.com/mcp/sse",
      "description": "Talent-Augmenting Layer — Remote MCP Server (Hosted)",
      "note": "This configuration connects to the remote-hosted MCP server. All users on this machine will share the same server instance."
    }
  }
}
```

**Key difference from local config**: Uses `"url"` instead of `"command"` and `"args"`.

---

## What You Get with Remote Access

### Tools
- `talent_get_profile(name)` — Load a user's AI augmentation profile
- `talent_get_calibration(name)` — Get calibration instructions for injecting into system prompts
- `talent_classify_task(description)` — Classify tasks into automate/augment/coach/protect
- `talent_log_interaction(user, task, engagement_level, outcome)` — Log interactions for skill tracking
- `talent_get_progression(name)` — Track skill progression over time
- `talent_list_profiles()` — List all available profiles
- `talent_status(name)` — Comprehensive status report for a user
- `talent_org_summary()` — Organization-level aggregation across all users
- `talent_save_profile(name, data)` — Create or update a profile
- `talent_delete_profile(name)` — Delete a profile
- `talent_assess_start()` — Start an onboarding assessment
- `talent_suggest_domains(role, industry)` — Suggest expertise domains

### Resources
- `talent://profile/{name}` — The full profile as markdown
- `talent://system-prompt/{name}` — Complete system prompt with profile injected
- `talent://coaching-modules` — Available coaching session modules

### Prompts
- `talent-system` — Full system prompt with profile for any LLM
- `talent-assess` — Interactive onboarding assessment
- `talent-coach` — Coaching session prompt
- `talent-update` — Profile update prompt

Assessment/coaching/update conversations in this flow are run by the model in your MCP client (for example, your selected Claude Code model). The remote MCP server provides tools, prompts, resources, and storage. It does not require you to provide a hosted Gemini/OpenAI/Anthropic key for the MCP prompt workflow.

### Claude Code Slash Commands

These are separate from MCP prompts and come from `.claude/commands/`:
- `/talent-assess`
- `/talent-update`
- `/talent-coach`

They load only when Claude Code is running in this repository, or when the files are copied into your own `~/.claude/commands/` directory.

---

## Troubleshooting

### "Connection refused" or "Server not responding"

1. **Verify the URL is correct**: `https://proworker-hosted.onrender.com/mcp/sse`
2. **Check the hosted app is running**: Visit `https://proworker-hosted.onrender.com` in your browser
3. **Check your internet connection**
4. **Restart your IDE**

### "No MCP tools found"

1. Check that your configuration file is valid JSON (copy from the file again)
2. Ensure the IDE config file is in the correct location
3. Confirm you used your IDE's MCP settings file, not a generic `config.json`
4. Restart your IDE completely
5. Check IDE logs for errors

### "Slash commands are missing"

1. Verify you opened this repository in Claude Code, not just added the MCP server globally
2. Confirm the `.claude/commands/` directory is present in the workspace
3. If you want the commands everywhere, copy the `.claude/commands/*.md` files into `~/.claude/commands/`
4. Remember: the remote MCP server exposes prompts and tools, but it does not install slash commands on its own

### "Could not load credentials from any providers"

1. In remote MCP mode, this usually means the client tried to use a hosted web-app assessment path instead of the MCP prompt/tool flow
2. Use MCP prompts/tools (`talent-assess`, `talent-coach`, `talent-update`, `talent_assess_start`, etc.) from your Claude Code session
3. The assessment conversation should be produced by your selected Claude Code model, not a hosted provider API
4. Hosted provider keys are only needed for the separate web app assessment routes, not for MCP prompt-driven usage

### "Tool calls fail with 400 Bad Request"

1. The MCP server may be under heavy load — wait a moment and try again
2. Verify you're using the correct tool names (see list above)
3. Check your tool arguments match the documented format

### Performance Issues

- Remote access is slightly slower than local (network latency)
- Typical latency: 200-500ms per request
- For heavy workloads, consider running locally

---

## API Endpoints (For Advanced Users)

The hosted app exposes these endpoints for direct HTTP access:

- `GET https://proworker-hosted.onrender.com/mcp/sse` — SSE connection endpoint
- `GET https://proworker-hosted.onrender.com/mcp/config` — Configuration instructions

Example usage (from a terminal or script):

```bash
# Get the remote MCP configuration
curl https://proworker-hosted.onrender.com/mcp/config
```

Output:
```json
{
  "type": "sse",
  "url": "https://proworker-hosted.onrender.com/mcp/sse",
  "description": "Talent-Augmenting Layer — Remote MCP Server",
  "supported_clients": [
    "Claude Desktop",
    "Cursor",
    "VSCode with MCP extension"
  ]
}
```

---

## Security & Privacy

- **Shared profiles**: All users on the same hosted instance share the same profile database
- **No authentication** currently required for the MCP endpoint
- **HTTPS**: All connections are encrypted in transit
- **Data storage**: Profiles are stored on the hosted database (see hosted/README.md for details)

---

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review `hosted/README.md` for hosted app setup
3. Review `mcp-server/README.md` for MCP server details
4. Open an issue: https://github.com/angelo-leone/talent-augmenting-layer/issues

---

## Migration from Local to Remote

If you're currently using local MCP:

1. Save any important profiles (export them from your local instance)
2. Update your IDE configuration file to use the remote config
3. Your profiles will be available on the shared hosted instance
4. You can still run local MCP for development (see Option 2 above)

---

## Next Steps

- **For non-technical people**: Copy the remote config file to your IDE and restart
- **For organizations**: Link all team members to the same hosted instance for shared profiles
- **For developers**: Set up local MCP for testing + use remote MCP for deployment (see hybrid setup in mcp-server/README.md)
