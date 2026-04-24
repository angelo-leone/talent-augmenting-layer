#!/usr/bin/env python3
"""TAL ambient-coaching SessionStart hook.

Injects the Talent-Augmenting Layer system prompt plus the resolved user
profile into the Claude Code session on startup, so coaching is active on
every turn without the user having to invoke a slash command.

Profile resolution order:
1. $PWD/profiles/pro-*.md or tal-*.md (project-local)
2. ~/.talent-augmenting-layer/profiles/pro-*.md or tal-*.md (global)

If no profile is found, the hook still injects the system prompt and points
the user at /talent-augmenting-layer:talent-assess.
"""
import glob
import json
import os
import sys


def load_system_prompt() -> str:
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    path = os.path.join(plugin_root, "tal-system-prompt.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, OSError):
        return ""


def load_profile() -> tuple[str, str | None]:
    candidates: list[str] = []
    search_dirs = [
        os.path.join(os.getcwd(), "profiles"),
        os.path.expanduser("~/.talent-augmenting-layer/profiles"),
    ]
    for base in search_dirs:
        candidates.extend(sorted(glob.glob(os.path.join(base, "pro-*.md"))))
        candidates.extend(sorted(glob.glob(os.path.join(base, "tal-*.md"))))
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                return content, path
        except OSError:
            continue
    return "", None


def main() -> None:
    system_prompt = load_system_prompt()
    if not system_prompt:
        sys.exit(0)

    profile, profile_path = load_profile()
    if profile:
        profile_section = (
            f"# Active User Profile\n\n_Loaded from `{profile_path}`._\n\n{profile}"
        )
    else:
        profile_section = (
            "# Active User Profile\n\n"
            "_No TAL profile found on this machine. If you already ran the "
            "assessment on the hosted web app (proworker-hosted.onrender.com) "
            "or via the remote MCP, run `/talent-augmenting-layer:talent-pull` "
            "to download it into the local cache. Otherwise run "
            "`/talent-augmenting-layer:talent-assess` to build one — takes "
            "~15 minutes._"
        )

    context = f"{system_prompt}\n\n---\n\n{profile_section}"

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
