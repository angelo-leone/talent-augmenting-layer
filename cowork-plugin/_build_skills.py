#!/usr/bin/env python3
"""Assemble the Cowork plugin's self-contained skills.

Cowork does not run plugin SessionStart hooks, so there is no ambient
injection of the TAOS system prompt the way the Claude Code plugin does
(via plugin/hooks/inject-tal-layer.py). Instead, every Cowork skill is
self-contained: its body carries the full TAOS system prompt followed by
the skill-specific protocol. Invoking any skill primes the model with the
complete coaching layer for the rest of the conversation, with no hooks
and no manual paste into Cowork's Global Instructions.

Source of truth (hand-edited):
  - plugin/tal-system-prompt.md        the TAOS system prompt
  - cowork-plugin/protocols/<name>.md  per-skill frontmatter + protocol body

Output (generated, do NOT hand-edit):
  - cowork-plugin/skills/<name>/SKILL.md

Re-run after editing either source. Idempotent.

    python3 cowork-plugin/_build_skills.py
"""
from __future__ import annotations

from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent
REPO_ROOT = PLUGIN_DIR.parent
SYSTEM_PROMPT = REPO_ROOT / "plugin" / "tal-system-prompt.md"
PROTOCOLS_DIR = PLUGIN_DIR / "protocols"
SKILLS_DIR = PLUGIN_DIR / "skills"

PREAMBLE = (
    "> The text below, up to the horizontal rule, is your complete operating "
    "instruction set as a Talent-Augmenting OS. Adopt it for the entire "
    "conversation, not just this skill. The skill-specific protocol follows "
    "the rule."
)


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_block, body).

    frontmatter_block includes the surrounding `---` fences. Matching is
    line-based so a stray `---` inside a description cannot break it.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("protocol file missing opening frontmatter fence")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            frontmatter = "".join(lines[: i + 1]).rstrip()
            body = "".join(lines[i + 1:]).lstrip("\n")
            return frontmatter, body
    raise ValueError("protocol file frontmatter never closed")


def main() -> None:
    if not SYSTEM_PROMPT.exists():
        raise SystemExit(f"system prompt not found: {SYSTEM_PROMPT}")
    system_prompt = SYSTEM_PROMPT.read_text(encoding="utf-8").strip()

    protocols = sorted(PROTOCOLS_DIR.glob("*.md"))
    if not protocols:
        raise SystemExit(f"no protocol fragments found in {PROTOCOLS_DIR}")

    for protocol_path in protocols:
        name = protocol_path.stem
        frontmatter, body = split_frontmatter(
            protocol_path.read_text(encoding="utf-8")
        )
        assembled = (
            f"{frontmatter}\n\n"
            f"{PREAMBLE}\n\n"
            f"{system_prompt}\n\n"
            f"---\n\n"
            f"{body.rstrip()}\n"
        )
        out_dir = SKILLS_DIR / name
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "SKILL.md"
        out_path.write_text(assembled, encoding="utf-8")
        print(f"  {out_path.relative_to(REPO_ROOT)}  ({len(assembled):,} chars)")

    print(
        f"Built {len(protocols)} Cowork skill(s) from "
        f"{SYSTEM_PROMPT.relative_to(REPO_ROOT)}"
    )


if __name__ == "__main__":
    main()
