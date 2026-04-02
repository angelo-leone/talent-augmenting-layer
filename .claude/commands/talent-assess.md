# /talent-assess

Remote MCP only.

1. Call `talent_assess_start`.
2. Run the assessment conversationally, one section at a time.
3. After collecting answers, call `talent_assess_score`.
4. Then call `talent_assess_create_profile`.
5. Keep the tone warm, concise, and Socratic.

If you see a provider credential error, switch back to MCP prompts/tools (`talent-assess`, `talent_assess_start`, etc.) so the assessment runs in the current Claude Code model session.
