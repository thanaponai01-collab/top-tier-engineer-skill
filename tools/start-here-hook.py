#!/usr/bin/env python3
"""
start-here-hook — SessionStart hook that hands a fresh session the project's current decisions.

Claude Code already loads CLAUDE.md, and with it the start-here block that links the project's
notes. This hook adds the two things a new session most often gets wrong by not reading further:
the decisions in force (`## Decisions` in BRIEF.md) and the next step (`## Next` in BUILD.md).
It also names any note over its line budget (recall's context_budget.py), so bloat is seen the
session it appears rather than when the file is already unreadable.

Available through hooks/optional.json and hooks/autonomous.json; the default install runs no hooks.

Channel: plain stdout on exit 0, which Claude Code adds to context for SessionStart. A project with
no BRIEF.md decisions, no BUILD.md next step and nothing over budget prints nothing.

Fails open, always. Exit 2 on SessionStart prevents the session from starting, so every error path
exits 0 and prints nothing.

Usage:  SessionStart hook (payload on stdin; its `cwd` is the project)
        start-here-hook.py --selftest [repo]
"""
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
BUDGET_SCRIPT = PLUGIN_ROOT / "skills" / "recall" / "scripts" / "context_budget.py"
MAX_LINES = 25

HEADER = ("Project notes loaded by the top-tier-engineer start-here hook. Decisions in force "
          "override older code, comments and notes; change one only by replacing its line in "
          "BRIEF.md and moving the old one to BRIEF.archive.md.")


def read(path):
    try:
        return Path(path).read_text(encoding="utf-8-sig", errors="replace")
    except (OSError, ValueError):
        return ""


def section(text, title):
    """Body of `## <title>` up to the next `## ` heading, trimmed; '' when absent."""
    m = re.search(rf"(?ims)^##\s+{re.escape(title)}\b[^\n]*$(.*?)(?=^##\s|\Z)", text)
    if not m:
        return ""
    body = [l for l in m.group(1).strip("\n").splitlines() if l.strip()]
    if len(body) > MAX_LINES:
        body = body[:MAX_LINES] + [f"… {len(body) - MAX_LINES} more lines in the file"]
    return "\n".join(body)


def over_budget(repo):
    """Lines naming each note over budget, via recall's context_budget.py; [] if unavailable."""
    try:
        spec = importlib.util.spec_from_file_location("context_budget", BUDGET_SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        rows = mod.measure(str(repo))
    except Exception:
        return []
    return [f"- {r['file']}: {r['lines']}/{r['budget']} lines → {r['fix']}" for r in rows if r["over"]]


def summary(repo):
    repo = Path(repo)
    parts = []
    decisions = section(read(repo / "BRIEF.md"), "Decisions")
    if decisions:
        parts.append("## Decisions in force (BRIEF.md)\n" + decisions)
    nxt = section(read(repo / "BUILD.md"), "Next")
    if nxt:
        parts.append("## Next (BUILD.md)\n" + nxt)
    over = over_budget(repo)
    if over:
        parts.append("## Notes over their line budget — trim before adding to them\n" + "\n".join(over))
    return HEADER + "\n\n" + "\n\n".join(parts) if parts else ""


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (OSError, ValueError):
        payload = {}
    repo = payload.get("cwd") if isinstance(payload, dict) else None
    text = summary(repo or os.getcwd())
    if text:
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass
        print(text)
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass
        args = [a for a in sys.argv[1:] if a != "--selftest"]
        print(summary(args[0] if args else os.getcwd()) or "start-here: nothing to load")
        sys.exit(0)
    try:
        sys.exit(main())
    except BaseException:
        sys.exit(0)
