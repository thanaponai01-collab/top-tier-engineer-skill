#!/usr/bin/env python3
"""
drive-entry — UserPromptSubmit hook for the autonomous profile (hooks/autonomous.json).

A skill that never loads does nothing. In evals/ROUTING.md the agent opened the right skill on its
own for 17 of 32 requests, and opened nothing at all for most bug, build and ship requests. For one
prompt to be trustworthy end to end, `drive` has to load first. `route-hint.py` only suggests a
skill and says skipping it needs no justification; this hook is the stronger, opt-in version for
runs nobody is watching: on a task-shaped prompt it tells the agent to load `drive` before any
other tool call.

Silent on: slash commands, prompts that already name a skill, short chat ("ok", "continue"), and
plain questions. Fails open, always: exit 2 on UserPromptSubmit blocks the prompt AND ERASES IT.

Usage:  UserPromptSubmit hook via hooks/autonomous.json (payload on stdin)
        drive-entry.py --selftest
"""
import json
import re
import sys
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
MIN_CHARS = 30
MAX_PROMPT = 20_000

_QUESTION_START = re.compile(
    r"^\s*(what|why|how|where|who|when|which|is|are|does|do|did|can|could|should|explain|show|tell|"
    r"describe|summari[sz]e)\b", re.I)
_TASK_CUE = re.compile(
    r"\b(fix|add|build|implement|change|make|update|refactor|ship|deploy|release|migrate|rename|"
    r"upgrade|remove|delete|rewrite|set up|sort (it|this|that) out|take this|get (it|this) (done|out)|"
    r"to done|figure out|broken|wrong|red|failing|fails|crash\w*|bug|slow|stopped|doesn.t work|"
    r"not working)\b", re.I)


def skill_names():
    try:
        return [p.name for p in SKILLS_DIR.iterdir() if (p / "SKILL.md").is_file()]
    except OSError:
        return []


def is_task(prompt):
    """True when the prompt reads as work to be done rather than a question or chatter."""
    if not isinstance(prompt, str):
        return False
    text = prompt.strip()[:MAX_PROMPT]
    if len(text) < MIN_CHARS or text.startswith("/"):
        return False
    if any(re.search(r"\b" + re.escape(n) + r"\b", text, re.I) for n in skill_names()):
        return False
    if _QUESTION_START.match(text) and text.rstrip().endswith("?"):
        return False
    return bool(_TASK_CUE.search(text))


MESSAGE = (
    "This prompt is a task. Before any other tool call, load the `drive` skill with the Skill tool "
    "and follow it: it matches a playbook, sets the exit check and the budget first, and parks "
    "anything irreversible (a deploy, a send, a delete) for a person. If this is really a typo, a "
    "rename or a plain question, say so in one line and work directly instead."
)


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if not isinstance(payload, dict) or not is_task(payload.get("prompt")):
        return 0
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError, OSError):
        pass
    print(MESSAGE)
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        assert is_task("Customers say their points are lower than they should be and the suite is red")
        assert is_task("Please fix the nightly digest so it stops dropping rows, I am offline until noon")
        assert not is_task("ok")
        assert not is_task("/drive fix the thing that is broken in the export")
        assert not is_task("why is the export slow when the table has a million rows?")
        assert not is_task("run debug-protocol on the export, it is broken somehow")
        print("selftest ok")
        sys.exit(0)
    try:
        sys.exit(main())
    except BaseException:
        sys.exit(0)
