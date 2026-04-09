# Privacy Policy

**Talent-Augmenting Layer (TAL)**
Last updated: 2026-04-09

## Overview

The Talent-Augmenting Layer (TAL) is an open-source MCP server that runs locally on your machine. It is designed with privacy as a core principle.

## Data Collection

**TAL does not collect, transmit, or share any personal data.** All data stays on your local machine.

### What is stored locally

When you use TAL, the following files are created and stored in your configured profiles directory (default: `~/.talent-augmenting-layer/profiles/`):

- **Profile files** (`tal-{name}.md`): Markdown files containing your assessment results, expertise ratings, task classifications, career goals, and calibration settings. These are human-readable and editable.
- **Interaction logs** (`log-{name}.jsonl`): JSONL files recording interaction metadata (task category, domain, engagement level, skill signals) used for skill progression tracking.

### What is NOT collected

- No telemetry is sent to any remote server
- No analytics or usage tracking
- No personal information leaves your machine
- No API keys are required or stored by the server itself
- No cookies, fingerprinting, or device identification

## Data Sharing

TAL does not share data with any third parties. The MCP server communicates exclusively with the MCP client running on your local machine (e.g., Claude Desktop) via the stdio transport protocol.

## Data Retention

All data persists only as local files. You can:

- View your profile at any time (it's a markdown file)
- Delete your profile and logs using the `talent_delete_profile` tool
- Manually delete files from the profiles directory

## Optional Remote Mode

If you choose to use the hosted version of TAL (via the remote MCP endpoint), your profile data is stored on the hosted server. The hosted version has its own authentication (Google OAuth) and database storage. Using the hosted version is entirely optional and separate from the desktop extension.

## Open Source

TAL is open source. You can inspect all code that handles your data at:
https://github.com/angelo-leone/talent-augmenting-layer

## Contact

For privacy questions or concerns, open an issue at:
https://github.com/angelo-leone/talent-augmenting-layer/issues
