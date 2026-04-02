# /talent-assess

Run a Talent-Augmenting Layer onboarding assessment. No remote API or MCP server required — the conversation runs in your current model session and results are saved locally.

## How it works

1. Read the full assessment protocol from `mcp-server/src/assessment.py` (the `get_assessment_protocol()` function, question banks `SECTION_A_QUESTIONS`, `SECTION_B_QUESTIONS`, `SECTION_D_QUESTIONS`, `ESA_ANCHORS`, and `suggest_domains()` domain taxonomy).
2. Read `profiles/TEMPLATE.md` for the output format.
3. Conduct the assessment conversationally, one section at a time:
   - **Identity**: name, role, organisation, industry, context summary
   - **Section A** (AI Dependency Risk): 5 questions with behavioural anchors (1-5 scale)
   - **Section B** (Growth Potential): 5 questions with behavioural anchors
   - **Section D** (AI Literacy): 4 questions with behavioural anchors
   - **Expertise Domains**: suggest domains based on role/industry using the taxonomy in assessment.py, ask user to rate each 1-5 using ESA scale, validate with behavioural examples. Aim for 5-10 domains.
   - **Goals & Context**: career goals, skills to develop, skills to protect, task classification (automate/augment/coach/protect/hands-off), red lines, learning/feedback/communication style preferences
4. Compute scores using the formulas in `assessment.py`: `compute_adr()`, `compute_gp()`, `compute_ali()`, `compute_esa()`, `compute_pwri()`, `compute_calibration()`, and `_apply_optimism_adjustment()`.
5. Generate the profile markdown using the `generate_profile_markdown()` template.
6. Save the profile to `profiles/pro-{name}.md` (lowercase, kebab-case).
7. Present the scores and ask: "Do these feel accurate? Anything you'd adjust?"

## Guidelines

- Be warm and conversational, not clinical
- Explain WHY you're asking each question briefly
- If the user gives a vague answer, probe with the behavioural anchors
- It's OK to adjust scores based on behavioural evidence (expert interviewer mode)
- The whole assessment should take 15-20 minutes
- If a profile already exists for this user, note it and confirm they want to replace it
