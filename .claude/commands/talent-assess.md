# /talent-assess

Run a Talent-Augmenting Layer onboarding assessment. Profile is always saved locally. MCP tools used for scoring when available.

## Flow

1. Read the assessment protocol from `mcp-server/src/assessment.py` (question banks `SECTION_A_QUESTIONS`, `SECTION_B_QUESTIONS`, `SECTION_D_QUESTIONS`, `ESA_ANCHORS`, domain taxonomy via `suggest_domains()`).
2. If a profile already exists in `profiles/pro-*.md` or `profiles/tal-*.md` for this user, note it and confirm they want to replace it.
3. Run the assessment conversationally, one section at a time.
4. Compute scores:
   - If MCP tools are available, call `talent_assess_score` with the raw answers.
   - Otherwise, use the formulas in `assessment.py` directly.
5. Generate the profile markdown (use `generate_profile_markdown()` template from `assessment.py`).
6. Save to `profiles/pro-{name}.md` (lowercase, kebab-case).
7. Present scores and ask: "Do these feel accurate? Anything you'd adjust?"

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
