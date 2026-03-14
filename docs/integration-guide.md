# Talent-Augmenting Layer — Integration Guide

> How to use Talent-Augmenting Layer with any LLM, agent, or tool.
> The portability story is the product differentiator.

---

## Architecture: 4 Tiers

```
┌─────────────────────────────────────────────────────────────────────┐
│  Tier 4: Hosted Web App                                             │
│  Google OAuth · LLM-powered assessment · email check-ins · DB       │
├─────────────────────────────────────────────────────────────────────┤
│  Tier 3: MCP Server (Claude Code, Cursor, Windsurf)                 │
│  14 tools · 5 resources · 3 prompts · automatic tracking            │
├─────────────────────────────────────────────────────────────────────┤
│  Tier 2: Platform-Native (Custom GPTs, Gems, Projects)              │
│  Pre-configured instances · persistent context · conversation starts│
├─────────────────────────────────────────────────────────────────────┤
│  Tier 1: Universal System Prompt (Any LLM)                          │
│  Copy-paste into any LLM · zero dependencies · works everywhere     │
└─────────────────────────────────────────────────────────────────────┘

All tiers share: same TALQ (14 fixed items + adaptive domains),
same scoring, same profile format, same behavioural rules.
```

---

## Tier 1: Universal System Prompt (Any LLM)

**What it is**: A self-contained system prompt and assessment prompt you can paste into any LLM that accepts custom instructions. No tools, no server, no dependencies.

**Setup (3 steps)**:

1. **Take the assessment**: Paste `universal-prompt/ASSESSMENT_PROMPT.md` into a conversation with any LLM. Answer the questions. The LLM generates your profile.
2. **Save your profile**: Copy the generated profile into `profiles/pro-yourname.md`
3. **Paste the system prompt**: Copy `universal-prompt/SYSTEM_PROMPT.md` (or the compact version `SYSTEM_PROMPT_COMPACT.md`) into your LLM's custom instructions, along with your profile

**Files**:

| File | Purpose |
|------|---------|
| `universal-prompt/SYSTEM_PROMPT.md` | Full system prompt (~4k tokens) |
| `universal-prompt/SYSTEM_PROMPT_COMPACT.md` | Compact system prompt for token-limited platforms (~2k tokens) |
| `universal-prompt/ASSESSMENT_PROMPT.md` | Self-contained assessment — paste into any LLM to generate your profile |
| `universal-prompt/QUICK_START.md` | Step-by-step setup instructions |

**Platform examples**:

| Platform | Where to paste |
|----------|---------------|
| ChatGPT | Settings > Personalization > Custom Instructions |
| Claude web | Project instructions or system prompt |
| Gemini | Custom instructions |
| Any LLM API | `system` parameter in API call |
| Perplexity, Copilot, etc. | Custom instructions / system prompt field |

**Profile updates**: At the end of a session, ask the LLM to output a `PROFILE UPDATE BLOCK`. Copy any changes back into your profile file manually.

**Limitations**: Manual profile sync between platforms; no automatic interaction logging; no server-side scoring.

---

## Tier 2: Platform-Native (Custom GPTs, Gems, Projects)

**What it is**: Pre-configured instances on major LLM platforms that include the system prompt and assessment flow built in. Users get persistent context, conversation starters, and a smoother experience than manual paste.

### ChatGPT Custom GPT

Reference file: `platform-configs/chatgpt-gpt.json`

1. Go to **Explore GPTs > Create** in ChatGPT
2. Import or paste the configuration from `chatgpt-gpt.json`
3. The GPT includes: system instructions, conversation starters, and assessment flow
4. Users interact with the GPT naturally; the profile is stored in the conversation context

### Gemini Gem

Reference file: `platform-configs/gemini-gem.md`

1. Go to **Gem Manager > Create** in Google Gemini
2. Follow the setup instructions in `gemini-gem.md`
3. Paste the system prompt and configure conversation starters
4. Gem persists the instructions across conversations

### Claude Project

Reference file: `platform-configs/claude-project.md`

1. Create a new **Project** in Claude (web or desktop)
2. Add the system prompt from `claude-project.md` as project instructions
3. Upload the user's profile as a project knowledge file
4. All conversations within the project use the Talent-Augmenting Layer behaviour

**Advantages over Tier 1**:
- Persistent context (no re-pasting each session)
- Conversation starters guide users to assessment and coaching flows
- Platform-native features (GPT store distribution, Gem sharing, Project collaboration)

**Profile updates**: Same as Tier 1 — LLM outputs `PROFILE UPDATE BLOCK` at session end. User updates their profile file or re-uploads to the platform.

---

## Tier 3: MCP Server (Claude Code, Cursor, Windsurf)

**What it is**: A full tool integration layer that exposes Talent-Augmenting Layer as 14 MCP tools, 5 resources, and 3 prompts. Provides automatic interaction tracking, server-side scoring, and programmatic profile management.

### Setup

1. **Install the server**:
```bash
cd talent-augmenting-layer/mcp-server
pip install -e .
```

2. **Add to your MCP client config**:

For **Claude Code** (`.claude/settings.json`):
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

For **Cursor** (`.cursor/mcp.json`):
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

For **Windsurf**, add the same server configuration in MCP settings.

For **Claude Desktop** (`claude_desktop_config.json`):
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

3. **Run the assessment**: Use `/talent-assess` (slash command) or call `talent_assess_start` via MCP

### Tools (14 total)

| Tool | Input | Output |
|------|-------|--------|
| `talent_get_profile` | `{name}` | Full profile markdown |
| `talent_get_calibration` | `{name}` | Compact calibration JSON for system prompt injection |
| `talent_classify_task` | `{name, task_description}` | Task classification + recommended AI behaviour |
| `talent_log_interaction` | `{name, category, domain, engagement, signal}` | Logged interaction entry for skill tracking |
| `talent_get_progression` | `{name}` | Skill progression stats, trends, atrophy warnings |
| `talent_list_profiles` | `{}` | List of all profile names |
| `talent_status` | `{name}` | Comprehensive status report |
| `talent_org_summary` | `{}` | Organisation-level aggregation across all profiles |
| `talent_delete_profile` | `{name}` | Delete profile + interaction logs |
| `talent_save_profile` | `{name, content}` | Save raw profile markdown to disk |
| `talent_assess_start` | `{name?}` | Full assessment protocol (questions + instructions) |
| `talent_assess_score` | `{answers, domain_ratings}` | Computed scores (ADR, GP, ALI, ESA, TALRI) |
| `talent_assess_create_profile` | `{name, role, org, ...}` | Generated profile saved to disk |
| `talent_suggest_domains` | `{role, industry, responsibilities?}` | Suggested expertise domains from industry taxonomy |

### Resources (5 total)

| URI | Content |
|-----|---------|
| `talent://profile/{name}` | Full profile markdown |
| `talent://system-prompt/{name}` | CLAUDE.md + profile (ready for any LLM) |
| `talent://coaching-modules` | Structured coaching sessions (5 modules, 13 sessions) |
| `talent://framework` | Assessment framework and methodology |
| `talent://literature` | Research literature backing the system |

### Prompts (3 total)

| Prompt | Description |
|--------|-------------|
| `talent-system` | Full system prompt for any LLM (CLAUDE.md + user profile) |
| `talent-assess` | Onboarding assessment (chatbot-driven, conversational) |
| `talent-coach` | Coaching session (with optional focus domain) |

### Slash Commands

| Command | Action |
|---------|--------|
| `/talent-assess` | Run initial assessment or full re-assessment |
| `/talent-coach` | Start a targeted coaching session on a specific skill |
| `/talent-update` | Update profile based on recent interactions |

**Profile updates**: Automatic via `talent_log_interaction`. The server tracks interaction patterns, engagement levels, and skill signals. Profile updates are applied through `talent_save_profile`.

**Advantages over Tier 2**:
- Automatic interaction tracking and skill progression analysis
- Server-side scoring (TALQ scores computed by the assessment engine)
- Organisation-level analytics via `talent_org_summary`
- Domain suggestion engine (`talent_suggest_domains`)
- Programmatic profile management (create, read, update, delete)
- Works with any MCP-compatible client

---

## Tier 4: Hosted Web App

**What it is**: A standalone web application with persistent user profiles, Google OAuth authentication, LLM-powered conversational assessment, 2-week email check-in reminders, and profile export. No LLM client required — works in any browser.

### Features

- **Google OAuth login**: Users authenticate via Google; no password management needed
- **LLM-powered assessment**: Conversational onboarding driven by an LLM (configurable provider)
- **Persistent profiles**: Stored in a database with full version history
- **2-week check-ins**: Automated email reminders prompt users to update their profile
- **Profile export**: Download profile as portable markdown for use in any tier
- **Dashboard**: Visual summary of scores, growth trajectory, and skill status

### Setup

1. **Environment variables** (see `hosted/README.md` for full list):
   - `SECRET_KEY`: Flask session secret
   - `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`: OAuth credentials
   - `LLM_PROVIDER` / `LLM_API_KEY`: LLM for conversational assessment
   - `SMTP_*`: Email configuration for check-in reminders
   - `DATABASE_URL`: Database connection string

2. **Google Cloud OAuth**: Create OAuth 2.0 credentials in Google Cloud Console. Add authorized redirect URIs.

3. **Deployment options**:

   **Docker** (recommended):
   ```bash
   cd hosted
   docker build -t talent-augmenting-layer-hosted .
   docker run -p 5000:5000 --env-file .env talent-augmenting-layer-hosted
   ```

   **Direct**:
   ```bash
   cd hosted
   pip install -r requirements.txt
   python app.py
   ```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Landing page / login |
| `/auth/login` | GET | Google OAuth login flow |
| `/assessment` | GET/POST | Conversational assessment interface |
| `/dashboard` | GET | User profile dashboard |
| `/checkin` | GET/POST | 2-week check-in form |
| `/api/profile/export` | GET | Export profile as markdown |

**Profile updates**: Automatic via database. Email reminders prompt 2-week check-ins. Full profile version history is maintained.

**Advantages over Tier 3**:
- No CLI or MCP client required — browser-only
- Built-in authentication and user management
- Automated email check-in reminders
- Profile versioning and history
- Suitable for non-technical users and organisational rollouts

---

## Profile Format (Cross-Platform Contract)

The profile is the portable unit. All four tiers produce and consume the same 9-section markdown format:

```markdown
# Talent-Augmenting Layer Profile: {Name}

## 1. Identity & Context
Role, organisation, industry, context summary

## 2. Expertise Map
Domain → Level (Novice/Developing/Proficient/Advanced/Expert) + AI mode

## 3. AI Relationship Status (Calibration)
TALQ scores: ADR, GP, ALI, ESA, TALRI
YAML calibration block with friction levels and behavioural settings

## 4. Growth Trajectory
Career goals, skills to develop, skills to protect

## 5. Interaction Preferences
Learning style, feedback style, communication style

## 6. Task Classification
automate / augment / coach / protect / hands-off task lists

## 7. Contrastive Knowledge
7.5. Domain-Specific Contrast Libraries (assumption → reality → principle tables)

## 8. Red Lines
Things AI should NEVER do for this user

## 9. Change Log
Dated entries tracking profile evolution
```

**Why markdown**: Portable across every platform, human-readable, works in any LLM's context window, easy to diff and version control. No proprietary format, no lock-in.

**Calibration YAML block** (embedded in Section 3):
```yaml
calibration:
  global_friction: 0.4        # 0 = full auto, 1 = full friction
  coaching_domains: [strategy, stakeholder_engagement]
  expert_domains: [economic_analysis, evaluation_design]
  protected_skills: [critical_thinking, writing]
  red_lines: [never_send_emails, never_make_final_decisions]
```

**Domain-specific contrast libraries** (Section 7.5): Tables mapping common assumptions to reality to transferable principles, organized by domain. These power the contrastive explanation engine in coaching and developing domains.

---

## Profile Sync Across Platforms

### Track A: LLM-Driven Session Updates (Tiers 1-2)

At the end of a substantive session, the LLM outputs a `PROFILE UPDATE BLOCK`:

```
--- PROFILE UPDATE BLOCK ---
Domain: strategy
Signal: growth
Evidence: User identified the counterfactual issue independently
Suggestion: Consider moving strategy from "coach" to "augment"
--- END PROFILE UPDATE BLOCK ---
```

The user copies relevant updates into their profile manually. This is the lowest-friction sync mechanism and works with any LLM.

### Track B: Server-Managed Sync (Tier 3)

The MCP server handles profile updates programmatically:
1. `talent_log_interaction` records every substantive interaction
2. `talent_get_progression` analyzes trends and flags atrophy risks
3. `/talent-update` (slash command) triggers a profile revision based on accumulated logs
4. `talent_save_profile` writes the updated profile to disk

### Track C: Hosted App Sync (Tier 4)

The hosted web app provides automated sync:
1. Profile changes are persisted to the database immediately
2. 2-week email reminders prompt users to review and update their profile
3. Full version history is maintained — users can compare profiles over time
4. Profile export produces the same portable markdown format used by all other tiers

### Manual Check-In Protocol

Regardless of tier, users should periodically review their profile:
- **Every 2 weeks**: Quick check — are the task classifications still accurate?
- **Every 2 months**: ADR check — have AI dependency patterns changed?
- **Every 6 months**: Full re-assessment via `/talent-assess` or ASSESSMENT_PROMPT.md

---

## Organisational Deployment

### Team Setup

1. **Choose a tier** (or combine tiers):
   - Small teams with MCP clients: Tier 3 (shared profiles directory)
   - Non-technical teams: Tier 4 (hosted web app)
   - Mixed environments: Tier 1/2 for LLM users + Tier 3 for developers

2. **Set up a shared profiles directory** (for Tier 3): network drive, Git repo, or S3 bucket

3. **Run onboarding** for each team member via MCP assessment or hosted app

4. **Use the Streamlit dashboard** (`dashboard/app.py`) for organisation-level monitoring:
   - Aggregate dependency risk across the team
   - Skill distribution heat maps
   - Atrophy alerts by domain
   - Growth trends over time

### Onboarding Flow for New Team Members

1. New member takes the TALQ assessment (via any tier)
2. Profile is generated and saved to the shared profiles directory
3. Member configures their LLM/IDE with the Talent-Augmenting Layer system prompt
4. First coaching session (`/talent-coach`) establishes the baseline
5. Regular check-ins track skill development over time

### Deployment Options

| Method | Complexity | Best For |
|--------|-----------|----------|
| Git repo + local MCP (Tier 3) | Low | Individual / small team |
| Shared profiles + per-machine MCP (Tier 3) | Medium | Office teams with MCP clients |
| Hosted web app (Tier 4) | Medium | Non-technical teams, org rollouts |
| Docker deployment (Tier 4) | Medium-High | Enterprise with existing infrastructure |
| Central MCP server (HTTP transport) | High | Enterprise MCP deployment |
| API wrapper service | High | SaaS product integration |

---

## MCP Server Reference

### Quick Reference: 14 Tools

| # | Tool | Purpose |
|---|------|---------|
| 1 | `talent_get_profile` | Load full profile markdown |
| 2 | `talent_get_calibration` | Get compact calibration JSON |
| 3 | `talent_classify_task` | Classify task into AI interaction mode |
| 4 | `talent_log_interaction` | Log interaction for skill tracking |
| 5 | `talent_get_progression` | Get skill progression stats and trends |
| 6 | `talent_list_profiles` | List all available profiles |
| 7 | `talent_status` | Comprehensive user status report |
| 8 | `talent_org_summary` | Organisation-level analytics |
| 9 | `talent_delete_profile` | Delete profile and logs |
| 10 | `talent_save_profile` | Save raw profile markdown |
| 11 | `talent_assess_start` | Start assessment protocol |
| 12 | `talent_assess_score` | Compute TALQ scores from raw answers |
| 13 | `talent_assess_create_profile` | Generate and save profile from assessment |
| 14 | `talent_suggest_domains` | Suggest expertise domains by role/industry |

### Quick Reference: 5 Resources

| URI | Content |
|-----|---------|
| `talent://profile/{name}` | Full profile markdown |
| `talent://system-prompt/{name}` | CLAUDE.md + profile |
| `talent://coaching-modules` | Structured coaching sessions |
| `talent://framework` | Assessment framework |
| `talent://literature` | Research literature |

### Quick Reference: 3 Prompts

| Prompt | Description |
|--------|-------------|
| `talent-system` | Full system prompt for any LLM |
| `talent-assess` | Chatbot-driven onboarding assessment |
| `talent-coach` | Targeted coaching session |
