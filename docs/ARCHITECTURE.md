# Talent-Augmenting Layer — Architecture

> A layered, platform-portable system. Same TALQ instrument, same scoring, same profile format across every entry point.

---

## System Diagram (Mermaid)

```mermaid
flowchart TB
  %% ───────── Entry points ─────────
  subgraph ENTRY["User Entry Points"]
    direction LR
    U1["Any LLM<br/>(ChatGPT · Gemini · Claude web)<br/>Universal system prompt"]
    U2["Platform-native<br/>Custom GPT · Gemini Gem<br/>Claude Project"]
    U3["Claude Code / Cursor / Windsurf<br/>Slash commands<br/>/talent-assess · /coach · /update"]
    U4["Claude Desktop<br/>Desktop Extension (.mcpb)<br/>MCP Connector"]
    U5["Claude Cowork Plugin<br/>.claude-plugin marketplace<br/>One-click install"]
    U6["Hosted Web App<br/>Browser · Google OAuth<br/>proworker-hosted.onrender.com"]
  end

  %% ───────── Orchestration ─────────
  subgraph LLM["LLM Orchestration"]
    direction LR
    L1["Claude (Code / Desktop)"]
    L2["Gemini 2.5 Flash-Lite<br/>(hosted assessment)"]
    L3["Any LLM<br/>(via system prompt)"]
  end

  %% ───────── TAL Core ─────────
  subgraph CORE["TAL Core Logic"]
    direction TB
    MCP["MCP Server<br/>mcp-server/src/server.py<br/>14 tools · 5 resources · 4 prompts"]
    ASSESS["Assessment Engine<br/>TALQ · ADR / GP / ALI / ESA / TALRI"]
    CLASSIFY["Task Classifier<br/>automate · augment · coach<br/>protect · hands-off"]
    TRACK["Interaction Logger<br/>engagement · skill signal<br/>atrophy detection"]
    CONTRAST["Contrastive Explanation<br/>Engine"]
  end

  %% ───────── Transports ─────────
  subgraph TRANSPORT["MCP Transports"]
    direction LR
    T1["stdio<br/>(local)"]
    T2["Streamable HTTP + SSE<br/>(remote)"]
    T3["OAuth 2.1 + PKCE<br/>(Google)"]
  end

  %% ───────── Storage ─────────
  subgraph STORE["Profile & Telemetry Storage"]
    direction LR
    S1["Local<br/>~/.talent-augmenting-layer/<br/>profiles/pro-*.md<br/>*.interactions.jsonl"]
    S2["PostgreSQL (Render)<br/>User · Profile · Session<br/>ChatLog · Check-in · Survey"]
  end

  %% ───────── External ─────────
  subgraph EXT["External Services"]
    direction LR
    E1["Google OAuth"]
    E2["Google Drive<br/>(anonymised export)"]
    E3["SendGrid<br/>(check-in reminders)"]
  end

  %% ───────── Edges ─────────
  U1 --> L3
  U2 --> L3
  U3 --> L1
  U4 --> L1
  U5 --> L1
  U6 --> L2

  L1 --> MCP
  L2 --> MCP
  L3 -.profile only.-> S1

  U3 --> T1
  U4 --> T2
  U5 --> T2
  T2 --> T3
  T1 --> MCP
  T2 --> MCP

  MCP --> ASSESS
  MCP --> CLASSIFY
  MCP --> TRACK
  MCP --> CONTRAST

  ASSESS --> S1
  ASSESS --> S2
  TRACK --> S1
  TRACK --> S2

  T3 --> E1
  S2 --> E2
  S2 --> E3
```

---

## Tier Overview

| Tier | Surface | Transport | Storage | Setup |
|------|---------|-----------|---------|-------|
| **1** | Any LLM | Copy-paste prompt | Profile pasted into custom instructions | 2 min |
| **2** | Custom GPT / Gem / Claude Project | Platform-native | Profile in project context | 5 min |
| **3a** | Claude Code / Cursor / Windsurf | MCP stdio | Local `~/.talent-augmenting-layer/` | 10 min |
| **3b** | Claude Desktop | Desktop Extension (.mcpb) | Local | 1-click |
| **3c** | Claude Cowork plugin | `.claude-plugin` marketplace | Local | 1-click |
| **3d** | Remote MCP clients | Streamable HTTP + OAuth | Hosted PostgreSQL | Sign-in |
| **4** | Hosted web app | HTTPS browser | PostgreSQL + optional Drive export | Sign-in |

All tiers share the same 14-tool MCP surface and the same portable markdown profile.

---

## MCP Tool Surface (14 tools)

**Profile management** — `talent_get_profile`, `talent_get_calibration`, `talent_status`, `talent_list_profiles`, `talent_save_profile`, `talent_delete_profile`
**Assessment** — `talent_assess_start`, `talent_assess_score`, `talent_assess_create_profile`, `talent_suggest_domains`
**Runtime** — `talent_classify_task`, `talent_log_interaction`, `talent_get_progression`
**Org** — `talent_org_summary`
**Telemetry** — `talent_parse_telemetry` (extracts `<tal_log>` JSON from LLM responses)

---

## Key Files

- `mcp-server/src/server.py` — MCP tool surface (stdio + remote)
- `desktop-extension/manifest.json` — Claude Desktop `.mcpb` package
- `.claude-plugin/marketplace.json` + `plugin/` — Claude Cowork plugin
- `server.json` — MCP registry manifest (Streamable HTTP remote)
- `hosted/app.py` — FastAPI hosted web app
- `hosted/mcp_sse_handler.py` + `hosted/mcp_oauth.py` — Remote MCP transport + OAuth
- `render.yaml` — Deployed service + managed PostgreSQL
- `CLAUDE.md` — Behavioural system prompt loaded into every session
- `profiles/pro-*.md` — Portable markdown profile (the calibration layer)

---

## Data Flow: A Coaching Session

1. User runs `/talent-coach` in Claude Code.
2. Claude Code invokes the MCP server (stdio or remote).
3. Server calls `talent_get_profile` → loads `pro-{name}.md`.
4. Server calls `talent_classify_task` → returns `coach` mode for the target skill.
5. Claude generates a scaffolded response using contrastive explanations from the profile's contrast library.
6. `talent_log_interaction` records engagement + skill signal.
7. Over time, `talent_get_progression` surfaces growth or atrophy trends.
