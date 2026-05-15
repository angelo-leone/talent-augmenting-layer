---
name: talent-speed
description: Temporarily drop coaching/friction for a single task. Use when the user just needs an execution-mode AI (fast, no hypothesis checks, no contrastive teaching) for one off task like boilerplate, a policy stub, or a repetitive transform. Does not modify the profile.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - mcp__plugin_talent-augmenting-layer_talent-augmenting-layer__talent_log_interaction
  - mcp__plugin_talent-augmenting-layer_talent-augmenting-layer__talent_classify_task
---

# /talent-speed

Run the next task in execution mode, regardless of the user's default calibration. This is a per-task override, not a profile change.

## When to use

The user says one of: "speed mode", "just do it for this one", "skip coaching this time", "I need this fast", "don't coach me on this one", or explicitly invokes `/talent-speed`. Typical use cases:

- Boilerplate or templated deliverables the user is not trying to learn (ISO policy stubs, standard CHANGELOG entries, RFP filler).
- One-off format conversions or refactors where the user already knows the pattern.
- Deadlines where cognitive forcing would just cost time.

## What changes (for this task only)

- Skip the hypothesis check. Do not ask "what's your initial instinct?" before producing output.
- Skip contrastive explanation. Do not frame the output as "you might assume X, but Y applies because...".
- Execute. Produce the deliverable, annotated enough that the user can verify decisions, and stop.
- Epistemic rules still apply. Do not hallucinate, do not agree reflexively, do not use em-dashes / rule-of-three / filler. Speed mode is not a licence to lie or fluff.

## What does NOT change

- The user's profile. No edit, no changelog, no `talent_save_profile` call.
- Red lines. If the task falls on the red-line list (things the AI must never do for this user), refuse the task instead of entering speed mode. Tell the user: "This is on your red line list. /talent-speed does not override red lines. Want to remove the red line first, or shall I surface the decision for you to make?"
- The default mode. After this task, the next turn reverts to the calibration in the profile.

## Flow

1. If the user passed a task description inline (`/talent-speed <description>` or a natural-language request like "speed mode: write an ISO policy stub"), start executing. No preamble.
2. If they invoked `/talent-speed` alone, say: "Speed mode on for the next task. What do you need?" and wait.
3. Do the task. Short annotation of key decisions at the end.
4. **Log the override** (see below). This is the load-bearing step.
5. Briefly flag that speed mode has ended: "Back to normal calibration. Say /talent-speed again if you want to repeat the pattern."

Keep annotations terse. Do not pad with "Here's what I did..." paragraphs.

## Log the override (every time)

Speed mode is a real calibration signal. Repeated use in coaching or protected domains is exactly the de-skilling pattern this product exists to catch. Every invocation has to be recorded; otherwise the system can't tell whether the user is using speed mode legitimately (boilerplate, repetitive transforms) or quietly bypassing the coaching they asked for.

Best-effort call `talent_classify_task` with the task description to discover what the profile *would have done*. Then call `talent_log_interaction` with:

- `name`: user's name
- `task_category`: `automate` (that's what speed mode is for this turn, regardless of what the profile said)
- `domain`: the skill domain the task touched. If `talent_classify_task` returns a domain, use it; otherwise pick the closest match from the profile's expertise map.
- `engagement_level`: `passive` (the user delegated; no hypothesis check, no contrastive)
- `skill_signal`: `atrophy` if the would-have-been category was `coach` / `protect` / a GROW domain; else `none`
- `notes`: e.g. `"speed mode override. task: <one-line summary>. profile category would have been: <classify_task result>"`. Keep it terse but include enough for `/talent-update` to review the pattern later.

If MCP logging is unavailable, append one JSONL line to `profiles/log-<name>.jsonl` with the same shape. Logging must not block the user's task: if both fail, finish the task and warn the user once that the override wasn't recorded.
