# Pro Worker AI — Personalized AI Augmentation Layer

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![MCP Tools](https://img.shields.io/badge/MCP%20Tools-13-blue)]()
[![Research-Backed](https://img.shields.io/badge/Research--Backed-Yes-green)]()

> Make workers better, not dependent. A personalized AI coaching system that follows you everywhere.

---

## What Is This?

Pro Worker AI (PWA) is a **personalized AI augmentation layer** that transforms how AI interacts with you. Instead of treating you as a generic user, PWA:

1. **Assesses** your expertise, goals, work style, and growth areas
2. **Creates** a living profile that calibrates all AI interactions to YOUR context
3. **Adapts** — coaching you in areas where you're growing, accelerating you where you're expert, automating what should be automated, and protecting skills at risk of atrophying
4. **Evolves** — your profile updates as you grow, keeping the AI aligned with your changing needs

**The core insight**: AI that does everything for you makes you worse over time. AI that knows WHEN to help, WHEN to coach, WHEN to challenge, and WHEN to step back makes you permanently better.

---

## The Problem

Current AI tools have one mode: **maximum helpfulness**. This creates three failure patterns:

| Pattern | What Happens | Research Evidence |
|---------|-------------|-------------------|
| **De-skilling** | Workers lose skills they stop practicing | Clinicians using AI for 3 months performed WORSE after removal than before (2024-25 studies) |
| **Over-reliance** | Workers accept AI output without critical evaluation | Humans with AI perform better than humans alone but WORSE than AI alone — because they blindly accept wrong suggestions (Buçinca 2021) |
| **Autopilot** | Workers disengage from cognitive work | Junior employees who "just hand in" AI work perform worse than those who engage critically (Mollick 2023) |

**Pro Worker AI exists to prevent all three.**

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                    CLAUDE.md                         │
│         (Pro-Worker System Instructions)             │
│   Loads profile → Calibrates behavior → Adapts      │
└───────────────────────┬─────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  /proworker  │ │  /proworker  │ │  /proworker  │
│   -assess    │ │   -update    │ │   -coach     │
│              │ │              │ │              │
│ Initial      │ │ Evolve       │ │ Targeted     │
│ assessment   │ │ profile      │ │ coaching     │
│ → profile    │ │ over time    │ │ session      │
└──────┬───────┘ └──────┬───────┘ └──────────────┘
       │                │
       ▼                ▼
┌─────────────────────────────────────────────────────┐
│              profiles/pro-{name}.md                  │
│                                                      │
│  Identity · Expertise Map · AI Relationship Status   │
│  Growth Trajectory · Interaction Preferences          │
│  Task Classification · Calibration Settings           │
│  Red Lines · Change Log                              │
└─────────────────────────────────────────────────────┘
```

### The Five Modes

Every task gets classified into one of five AI interaction modes:

| Mode | AI Role | Friction | Example |
|------|---------|----------|---------|
| **Automate** | Execute + annotate | Low | Data cleanup, formatting, boilerplate |
| **Augment** | Accelerate + challenge | Low-Med | Research in expert domains, code in proficient areas |
| **Coach** | Scaffold + question | Med-High | Skills you're actively developing |
| **Protect** | Force cognition + teach | High | Skills at risk of atrophying from AI over-use |
| **Hands-off** | Don't touch | N/A | Tasks that are core to your human identity and judgment |

### Research-Backed Techniques

| Technique | Source | When Used |
|-----------|--------|-----------|
| **Cognitive Forcing** | Buçinca et al. (2021) | Novice domains, high-stakes decisions — ask for user's hypothesis first |
| **Contrastive Explanations** | Buçinca et al. (2024) | Learning moments — explain the DELTA between user's mental model and reality |
| **Adaptive Support** | Buçinca et al. (2024) | All interactions — adjust friction based on user state |
| **Expert Augmentation** | Mollick (2023) | Expert domains — skip basics, challenge assumptions, accelerate |
| **De-skilling Protection** | Multiple (2024-25) | Protected skills — add friction, require human-first attempts |

---

## Quick Start

### Option A: Claude Code (Full Experience)

1. Clone this repo
2. Add the MCP server to `.claude/settings.json`:
```json
{
  "mcpServers": {
    "proworker-ai": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/pro-worker-ai/mcp-server",
      "env": {
        "PROWORKER_PROFILES_DIR": "/path/to/pro-worker-ai/profiles"
      }
    }
  }
}
```
3. Run `/proworker-assess` to create your profile (the chatbot guides you through it)
4. Work normally — CLAUDE.md automatically calibrates every interaction

### Option B: Any MCP Client (Claude Desktop, Cursor, Windsurf, etc.)

1. Install: `cd mcp-server && pip install -e .`
2. Add the MCP server to your client's config (same JSON as above)
3. The chatbot can call `proworker_assess_start` to run the onboarding
4. Your profile is created and used for all future interactions

### Option C: Any LLM (ChatGPT, Gemini, etc.)

1. Read `proworker://system-prompt/yourname` from the MCP server
2. Paste into your LLM's system instructions / custom instructions
3. The AI will behave according to your Pro Worker AI profile

See `docs/integration-guide.md` for detailed platform-specific instructions.

### Day-to-Day Commands
- `/proworker-assess` — Run initial assessment or full re-assessment
- `/proworker-update` — Update profile based on recent interactions
- `/proworker-coach` — Start a targeted coaching session on a specific skill

---

## The Vision: A Universal Layer

Pro Worker AI is designed as a **layer** — not tied to any specific tool, LLM, or platform.

### Where It Can Go

| Platform | Implementation |
|----------|---------------|
| **Claude Code** | CLAUDE.md + slash commands (current) |
| **Any LLM** | Append the profile as system prompt context |
| **Agent frameworks** | Inject profile into agent system prompts |
| **MCP Server** | Serve profiles and assessment as MCP tools |
| **IDE extensions** | VS Code / Cursor extension that loads profile |
| **API middleware** | Intercept LLM calls, inject profile, apply friction |

The profile is **portable markdown** — it works anywhere you can inject system context.

### The Marketplace Opportunity (PUBLIC.io)

PWA could be a product on PUBLIC's marketplace:

1. **Assessment-as-a-Service**: Organizations run PWA assessments across their workforce
2. **Personalized AI Policies**: Instead of "everyone uses AI the same way," each worker gets calibrated AI interaction
3. **Skills Dashboard**: Track workforce skill development and AI dependency risk over time
4. **Compliance Layer**: Ensure AI usage in regulated sectors (healthcare, gov, finance) maintains human competence
5. **Training Integration**: Connect assessment results to L&D programs

---

## Research Foundation

Built on empirical research, not opinions:

| Source | Key Finding | How We Use It |
|--------|-------------|---------------|
| Buçinca et al. (2021) | Cognitive forcing reduces over-reliance by ~30% | Ask for hypothesis before revealing AI's answer |
| Buçinca et al. (2024) | Contrastive explanations improve skills +8% (d=0.35) | Explain delta between user's model and AI's |
| Buçinca et al. (2024) | Optimal AI support depends on individual state | Personalize via profile, adapt dynamically |
| Mollick et al. (2023) | AI: +40% quality, +26% speed — but juniors who "just hand in" do worse | Protect against autopilot, especially in growth areas |
| Drago & Laine (2025) | The Intelligence Curse: humans must stay complementary | Build skills that maintain human economic relevance |
| Acemoglu | Pro-worker AI should increase human marginal product | Every interaction should make the user more valuable |
| Vygotsky | Zone of Proximal Development | Scaffold just beyond current ability |
| Ericsson | Deliberate Practice | Practice at edge of ability with feedback |
| Deci & Ryan | Self-Determination Theory | Protect autonomy, build competence |
| Dweck | Growth Mindset | Frame friction as opportunity |

---

## File Structure

```
pro-worker-ai/
├── CLAUDE.md                           # Core system prompt (the brain)
├── README.md                           # This file
├── system_prompt.md                    # Original research-based prompt (v1)
├── .claude/
│   ├── commands/
│   │   ├── proworker-assess.md         # /proworker-assess slash command
│   │   ├── proworker-update.md         # /proworker-update slash command
│   │   └── proworker-coach.md          # /proworker-coach slash command
│   └── settings.local.json            # Claude Code permissions
├── mcp-server/                         # Cross-platform MCP server
│   ├── pyproject.toml                  # Package config
│   ├── README.md                       # MCP server docs
│   └── src/
│       ├── server.py                   # MCP tools, resources, prompts (13 tools)
│       ├── profile_manager.py          # Profile CRUD, parsing, interaction logging
│       └── assessment.py               # Embedded assessment engine (questions, scoring)
├── assessment/
│   ├── framework.md                    # Assessment methodology
│   ├── scoring-instrument.md           # PWAQ psychometric instrument
│   ├── coaching-modules.md             # Structured coaching sessions (5 modules, 13 sessions)
│   ├── ab-testing-framework.md         # A/B testing design for outcomes research
│   └── literature-foundations.md       # Research backing
├── dashboard/
│   └── app.py                          # Streamlit org-level analytics dashboard
├── web-ui/
│   └── index.html                      # Standalone web assessment UI
├── docs/
│   └── integration-guide.md            # Platform integration guides (7 platforms)
├── profiles/
│   ├── TEMPLATE.md                     # Blank profile template
│   └── pro-angelo.md                   # Example: Angelo's profile
├── context/                            # Research papers (Buçinca, Acemoglu, Mollick)
├── pro-worker-benchmark/               # PWI benchmark suite (separate tool)
└── paper/                              # Academic paper on PWI benchmark
```

---

## What Makes This Different From Memory?

Good question. Memory stores facts. **Pro Worker AI is how memory is used.**

| Feature | Plain Memory | Pro Worker AI |
|---------|-------------|---------------|
| Stores user info | Yes | Yes |
| Adapts AI behavior | No — just recalls | Yes — systematically calibrates every interaction |
| Protects skills | No | Yes — cognitive forcing, de-skilling prevention |
| Coaches growth | No | Yes — targeted scaffolding in growth areas |
| Classifies tasks | No | Yes — automate/augment/coach/protect/hands-off |
| Evolves over time | Appends facts | Tracks skill progression, adjusts calibration |
| Research-backed | No | Yes — grounded in HCI and workforce learning literature |

Memory is the database. **PWA is the operating system.**

---

## Contributing

This is an open-source personalized AI augmentation layer. Current status:

- [x] Core system prompt with 4 interaction modes (CLAUDE.md)
- [x] Interactive assessment with profile generation
- [x] Psychometric scoring instrument (PWAQ) with validated Likert scales
- [x] MCP server with 13 tools for cross-platform portability
- [x] Embedded chatbot-driven onboarding (any MCP client can run the assessment)
- [x] Organization-level dashboard (Streamlit)
- [x] Skill progression tracking with trend analysis and atrophy detection
- [x] Integration guides for 7 platforms (Claude, ChatGPT, Cursor, APIs, custom agents)
- [x] A/B testing framework for outcomes research
- [ ] HTTP transport for enterprise MCP deployment
- [ ] Integration with existing L&D platforms
- [ ] Multi-user benchmarking and anonymized comparisons
- [ ] API middleware for any LLM provider
- [ ] Mobile-friendly assessment UI

---

## License

This work is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-nc-sa/4.0/).

**You are free to** share and adapt this work for non-commercial purposes, as long as you give appropriate credit and distribute contributions under the same license.

See [LICENSE](LICENSE) for the full text.

---

## Citation

If you use Pro Worker AI in research or publications, please cite:

```bibtex
@software{leone2026proworkerai,
  author    = {Leone, Angelo},
  title     = {Pro Worker AI: A Personalized AI Augmentation Layer for Workforce Development},
  version   = {0.2.0},
  year      = {2026},
  url       = {https://github.com/angelo-leone/pro-worker-ai},
  license   = {CC-BY-NC-SA-4.0}
}
```

Or see [CITATION.cff](CITATION.cff) for machine-readable citation metadata.

---

*Built by Angelo Leone at PUBLIC. Powered by research from Buçinca, Acemoglu, Mollick, Drago & Laine.*
*Every interaction should leave you more capable, not more dependent.*

Copyright (c) 2026 Angelo Leone. All rights reserved under CC BY-NC-SA 4.0.
