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
4. Briefly flag that speed mode has ended: "Back to normal calibration. Say /talent-speed again if you want to repeat the pattern."

Keep annotations terse. Do not pad with "Here's what I did..." paragraphs.
