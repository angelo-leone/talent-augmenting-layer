# /talent-assess

Run a Talent-Augmenting Layer onboarding assessment. Profile is saved locally in `profiles/pro-{name}.md`. The MCP server is the source of truth for the question bank and scoring.

## First: greet the user before any tool calls

Before calling any tool, send a short greeting so the user sees activity:

> "Hi! I'll guide you through a ~15 minute assessment to build your personalised Talent-Augmenting Layer profile. Loading the question bank now — if the server has been idle, this first call can take 30–60 seconds to wake up. One moment."

Never go silent during setup.

## Flow

1. Call the MCP tool `talent_assess_start` to fetch the full question bank, scoring anchors, and domain taxonomy as JSON. This is the single source of truth — do NOT try to read `mcp-server/src/assessment.py` from the filesystem (participants who installed via the pilot guide don't have that file locally).
2. If `talent_assess_start` fails or times out after ~90 seconds, tell the user:
   > "The TAL server is taking a while to wake up. Open https://proworker-hosted.onrender.com in a browser tab, wait ~45 seconds for it to respond, then tell me 'retry' and I'll try again."
   Do not proceed without the protocol.
3. Check `profiles/pro-*.md` or `profiles/tal-*.md` in the current directory. If one exists for this user, confirm they want to replace it before continuing.
4. Run the assessment conversationally, one section at a time (see sections below). For the expertise-domain step, call `talent_suggest_domains` to get the taxonomy.
5. Compute scores by calling `talent_assess_score` with the raw answers and domain ratings.
6. Save the profile by calling `talent_assess_create_profile` with the scores plus qualitative data — it generates the markdown and writes it. If that call fails, fall back: generate the markdown from the template returned by `talent_assess_start` and Write it to `profiles/pro-{name}.md` (lowercase, kebab-case) in the current directory.
7. Present the scores and ask: "Do these feel accurate? Anything you'd adjust?"

## Assessment sections

- **Identity**: name, role, organisation, industry, context summary
- **Section A** (AI Dependency Risk): 5 questions, behavioural anchors 1-5
- **Section B** (Growth Potential): 5 questions, behavioural anchors 1-5
- **Section D** (AI Literacy): 4 questions, behavioural anchors 1-5
- **Expertise Domains**: suggest domains via `talent_suggest_domains` (or the taxonomy in assessment.py), rate each 1-5 on the ESA scale, validate with behavioural examples. Aim for 5-10 domains.
- **Goals & Context**: career goals, skills to develop/protect, task classification (automate/augment/coach/protect/hands-off), red lines, learning/feedback/communication style

## Guidelines

- Be warm and conversational, not clinical
- Explain WHY you're asking each question briefly
- If the user gives a vague answer, probe with the behavioural anchors
- It's OK to adjust scores based on behavioural evidence (expert interviewer mode)
- The whole assessment should take 15-20 minutes
- If a profile already exists, note it and confirm they want to replace it
