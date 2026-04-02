# /talent-assess

Run a Talent-Augmenting Layer onboarding assessment. Uses MCP tools when available, falls back to local files.

## Flow

### If the MCP server is connected (preferred)

1. Call `talent_assess_start` to get the full question bank and protocol.
2. Run the assessment conversationally, one section at a time.
3. After collecting all answers, call `talent_assess_score` with the raw answers.
4. Call `talent_assess_create_profile` to generate and save the profile.
5. Present scores and ask: "Do these feel accurate? Anything you'd adjust?"

### If no MCP server is connected (local fallback)

1. Read the assessment protocol from `mcp-server/src/assessment.py` (question banks, ESA anchors, domain taxonomy).
2. Run the assessment conversationally (same flow as above).
3. Compute scores using the formulas in `assessment.py`.
4. Generate the profile markdown and save to `profiles/pro-{name}.md`.
5. Also append an initial interaction log entry to `profiles/log-{name}.jsonl`.

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
