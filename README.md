# Pro Worker AI — Personalized AI Augmentation Layer

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

### 1. Install
Clone this repo into your project or copy the key files:
```
CLAUDE.md                          → Your project root
.claude/commands/proworker-assess.md  → Slash command
.claude/commands/proworker-update.md  → Slash command
.claude/commands/proworker-coach.md   → Slash command
assessment/framework.md            → Assessment questions
profiles/TEMPLATE.md               → Profile template
```

### 2. Run Assessment
In Claude Code, run:
```
/proworker-assess
```
This starts an interactive assessment (~10-15 minutes) that creates your personalized profile.

### 3. Work Normally
Once your profile exists, CLAUDE.md automatically:
- Loads your profile at the start of every conversation
- Calibrates friction levels per-domain
- Applies cognitive forcing in your growth areas
- Accelerates you in your expert domains
- Protects skills you've flagged as important

### 4. Update Periodically
Run `/proworker-update` every few weeks to evolve your profile based on how you've grown.

### 5. Targeted Coaching
Run `/proworker-coach` when you want a focused session on a specific skill.

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
├── assessment/
│   ├── framework.md                    # Assessment questions & methodology
│   └── literature-foundations.md       # Research backing for each dimension
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

This is early-stage. The system works now in Claude Code. Next steps:

- [ ] MCP server implementation for cross-platform portability
- [ ] Organization-level assessment and dashboard
- [ ] Skill progression tracking and visualization
- [ ] Integration with existing L&D platforms
- [ ] Multi-user benchmarking and anonymized comparisons
- [ ] API middleware for any LLM provider

---

## License

TBD — This is a product concept for PUBLIC.io.

---

*Built by Angelo at PUBLIC. Powered by research from Buçinca, Acemoglu, Mollick, Drago & Laine.*
*Every interaction should leave you more capable, not more dependent.*
