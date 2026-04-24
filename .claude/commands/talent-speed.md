# /talent-speed

Per-task override that drops coaching/friction for the next task only. No profile edit.

## When to use

The user says "speed mode", "just do it this time", "skip coaching", "I need this fast", or invokes `/talent-speed` for boilerplate, templated work, or deadline-driven output where cognitive forcing would just cost time.

## What changes (for this task only)

- Skip the hypothesis check. Do not ask "what's your initial instinct?" before producing output.
- Skip contrastive explanation.
- Execute. Produce the deliverable, annotated enough that the user can verify, and stop.
- Epistemic rules still apply. No hallucination, no reflexive agreement, no em-dashes / rule-of-three / filler.

## What does NOT change

- The user's profile. No edit, no changelog.
- Red lines. If the task is on the user's red-line list, refuse and tell them: "This is on your red line list. /talent-speed does not override red lines. Want to remove the red line first, or shall I surface the decision for you to make?"
- Default calibration. After this task, the next turn reverts.

## Flow

1. If a task was passed inline (`/talent-speed <description>`), start executing immediately.
2. If invoked alone, say "Speed mode on for the next task. What do you need?" and wait.
3. Do the task. Short annotation of key decisions at the end.
4. Flag that speed mode has ended: "Back to normal calibration. Say /talent-speed again if you want to repeat the pattern."

Keep annotations terse.
