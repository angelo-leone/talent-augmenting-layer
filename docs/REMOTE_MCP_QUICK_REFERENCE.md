# Remote MCP Quick Reference

## TL;DR — Get Access in 2 Minutes

### Step 1: Download Config
- **Claude Desktop**: `mcp-server/claude-desktop-config-remote.json`
- **Cursor/VSCode**: `mcp-server/claude-code-config-remote.json`

### Step 2: Paste Into IDE
- **Claude Desktop** → `~/.config/Claude Desktop/claude_desktop_config.json`
- **Cursor** → `~/.cursor/mcp_config.json`
- **VSCode** → (check Cursor docs)

### Step 3: Restart IDE
Close and reopen your IDE.

**That's it!** MCP tools now work.

---

## What You Get

| Feature | Available |
|---------|-----------|
| Load profiles | ✅ Yes |
| Run assessments | ✅ Yes |
| View system prompts | ✅ Yes |
| Track skill progression | ✅ Yes |
| Log interactions | ✅ Yes |
| Share profiles | ✅ Yes (Cloud DB) |
| Use from anywhere | ✅ Yes |
| No installation needed | ✅ Yes |

---

## Example Commands

In Claude Desktop or Cursor:

```
@talent.profile <name>
Load your AI profile

@talent.status <name>
Get a status report

@talent.list-profiles
See all available profiles

@talent.assess-start
Begin an assessment

@talent.get-calibration <name>
Get system prompt calibration for any LLM
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No MCP tools" | Restart IDE after pasting config |
| "Connection error" | Check URL is `https://proworker-hosted.onrender.com/mcp` |
| "Server not found" | Visit that URL in browser to verify it's running |
| "Slow responses" | Remote is ~200-500ms slower than local; that's normal |

---

## Support

- Full guide: `docs/REMOTE_MCP_SETUP.md` (start here for help)
- Technical: `mcp-server/README.md`
- Issues: https://github.com/angelo-leone/talent-augmenting-layer/issues

---

## Config File Contents

Just so you know what you're pasting:

```json
{
  "mcpServers": {
    "talent-augmenting-layer": {
      "url": "https://proworker-hosted.onrender.com/mcp",
      "description": "Talent-Augmenting Layer — Remote MCP Server (Hosted)"
    }
  }
}
```

That's it! It tells your IDE to connect to the remote MCP server instead of running it locally.

---

## Want to Run Locally Instead?

Skip remote config. Instead:

```bash
cd mcp-server
python -m src.server
```

Then use `claude-desktop-config.json` (the non-remote version) in your IDE.

But honestly, remote is easier! 😊
