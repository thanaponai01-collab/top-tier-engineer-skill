#!/usr/bin/env python3
"""
philosophy-hook — SessionStart hook that loads PHILOSOPHY.md into the session.

Why this exists: PHILOSOPHY.md is the one file that applies to every task, and
until now it only reached a session if the user hand-edited ~/.claude/CLAUDE.md
with an @import. Most people never do. Installing the plugin should be the whole
install.

Channel: plain stdout on exit 0. Claude Code adds stdout to the model's context
for SessionStart (and UserPromptSubmit) specifically; for other events stdout
goes only to the debug log. No JSON is emitted, so there is no output schema to
drift against.

Fails open, always. Exit 2 on SessionStart PREVENTS THE SESSION FROM STARTING,
so every error path here must still exit 0 and print nothing. A habit file is
never worth wedging someone's session over.

Usage:  SessionStart hook via hooks/hooks.json (payload on stdin, ignored)
        philosophy-hook.py --selftest
"""
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PHILOSOPHY = PLUGIN_ROOT / "PHILOSOPHY.md"

HEADER = (
    "The engineering habits below are loaded for this session by the "
    "top-tier-engineer plugin. Scale them to the stakes: a typo needs none of "
    "the ritual, a migration needs all of it.\n\n"
)


def philosophy_text(path=PHILOSOPHY):
    """The philosophy file with its context header, or '' if it can't be read."""
    try:
        body = Path(path).read_text(encoding="utf-8-sig").strip()
    except (OSError, ValueError, UnicodeDecodeError):
        return ""
    if not body:
        return ""
    return HEADER + body


def main():
    # stdin is the hook payload; this hook needs nothing from it, but the pipe
    # is drained so Claude Code never blocks writing to a full buffer.
    try:
        sys.stdin.read()
    except (OSError, ValueError):
        pass

    text = philosophy_text()
    if text:
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass
        print(text)
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        t = philosophy_text()
        print(f"philosophy loaded: {len(t)} chars" if t else "philosophy MISSING")
        sys.exit(0)
    try:
        sys.exit(main())
    except BaseException:
        # Never let this hook stop a session from starting.
        sys.exit(0)
