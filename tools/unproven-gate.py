#!/usr/bin/env python3
"""
unproven-gate — flags source files that were edited and never run.

The habit this catches is the one nobody asks a skill for: code changed, the
turn ended, and "it should work" stood in for a result. PHILOSOPHY.md #3 and
#7 both land here — decide what done looks like, then say how you know.

WHY UserPromptSubmit AND NOT Stop
---------------------------------
Stop is the semantically obvious event, and an earlier version of this plugin
used it (deleted in c479319: it linted the suite's own verdict lines and could
block a session over a malformed one — machinery that policed the auditor).
Two things ruled Stop out this time:

  1. Reaching the model from Stop means `decision: "block"`. The docs now list
     additionalContext for Stop; Anthropic's own security-guidance plugin says
     Stop is not in the hookSpecificOutput union and that emitting it there
     silently corrupts the payload (issue #2159). Unresolved contradiction —
     not worth betting a hook on.
  2. Blocking is the wrong answer anyway. A gate that can keep someone in a
     session they asked to leave gets uninstalled, and then it protects nobody.

UserPromptSubmit has neither problem: plain stdout on exit 0 is added to the
model's context, it is documented on both sides, and it fires at the start of
the next turn — the first moment the reminder is actually actionable.

WHAT COUNTS AS RUNNING
----------------------
Reading is not proving. `cat`, `grep`, `ls`, `git status` and friends are inert:
under bypass-permissions mode an agent reads files with Bash all turn long, and
counting those as proof would make this gate green on a session where nothing
executed at all.

Fails open, always. Exit 2 on UserPromptSubmit blocks the prompt AND ERASES IT,
so every error path here exits 0 with no output. Losing a user's typed prompt to
a linting bug is a far worse failure than missing a reminder.

Usage:  UserPromptSubmit hook via hooks/hooks.json (payload on stdin)
        unproven-gate.py --selftest
"""
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

# Only the tail of a transcript can matter: the rule compares the LAST edit
# against the LAST run, and an edit buried megabytes back is stale anyway.
TAIL_BYTES = 2_000_000

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

SOURCE_SUFFIXES = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte",
    ".go", ".rs", ".java", ".kt", ".scala", ".rb", ".php", ".cs", ".swift",
    ".c", ".h", ".cc", ".cpp", ".hpp", ".m", ".mm", ".sh", ".bash", ".ps1",
    ".sql", ".ex", ".exs", ".erl", ".clj", ".lua", ".dart", ".r",
}

# Commands that read or inspect. Running one proves nothing about the code.
INERT = {
    "cat", "bat", "head", "tail", "less", "more", "ls", "ll", "dir", "tree",
    "cd", "pwd", "echo", "printf", "which", "type", "file", "stat", "wc",
    "grep", "rg", "ag", "find", "fd", "sed", "awk", "cut", "sort", "uniq",
    "env", "export", "set", "true", "false", "date", "whoami", "clear",
    "mkdir", "touch", "cp", "mv", "ln", "chmod", "sleep",
}
# `git <sub>` is inert for these; `git push`, `git commit` etc. are not.
INERT_GIT = {
    "status", "log", "diff", "show", "branch", "remote", "config",
    "ls-files", "rev-parse", "blame", "describe", "stash", "fetch",
}


def _tail_lines(path, limit=TAIL_BYTES):
    """Last complete lines of a JSONL file, cheaply. [] if unreadable."""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            if size > limit:
                fh.seek(size - limit)
                fh.readline()  # drop the partial line the seek landed inside
            raw = fh.read()
    except (OSError, ValueError):
        return []
    return raw.decode("utf-8", errors="replace").splitlines()


def _tool_calls(lines):
    """(tool_name, input_dict) for every tool_use in the transcript, in order."""
    for line in lines:
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        message = entry.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            name = block.get("name")
            data = block.get("input")
            if isinstance(name, str):
                yield name, (data if isinstance(data, dict) else {})


def is_source(path_str):
    """True if this path is code, not prose or config."""
    if not isinstance(path_str, str) or not path_str:
        return False
    return Path(path_str).suffix.lower() in SOURCE_SUFFIXES


def _segments(command):
    """Split a shell line into its separately-executed commands."""
    out, buf = [], ""
    i = 0
    while i < len(command):
        two = command[i:i + 2]
        if two in ("&&", "||"):
            out.append(buf)
            buf = ""
            i += 2
            continue
        if command[i] in ";|\n":
            out.append(buf)
            buf = ""
            i += 1
            continue
        buf += command[i]
        i += 1
    out.append(buf)
    return [s.strip() for s in out if s.strip()]


def _strip_prefixes(tokens):
    """Index of the real command, past `FOO=bar` assignments and `sudo`."""
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token == "sudo":
            idx += 1
            continue
        head = token.split("/")[0]
        if "=" in head and not token.startswith("-"):
            idx += 1
            continue
        break
    return idx


def runs_something(command):
    """True if any segment of this command actually executes the system."""
    if not isinstance(command, str):
        return False
    for seg in _segments(command):
        tokens = seg.split()
        idx = _strip_prefixes(tokens)
        if idx >= len(tokens):
            continue
        head = Path(tokens[idx]).name.lower()
        if head == "git":
            sub = tokens[idx + 1].lower() if idx + 1 < len(tokens) else ""
            if sub in INERT_GIT:
                continue
            return True
        if head in INERT:
            continue
        return True
    return False


def unproven_files(lines):
    """Source files edited after the last real run. Empty when all is proven."""
    last_run = -1
    edits = {}  # path -> index of its most recent edit
    for index, (tool, data) in enumerate(_tool_calls(lines)):
        if tool == "Bash" and runs_something(data.get("command")):
            last_run = index
        elif tool in EDIT_TOOLS:
            target = data.get("file_path") or data.get("notebook_path")
            if is_source(target):
                edits[target] = index
    return sorted(path for path, index in edits.items() if index > last_run)


def _already_warned(session_id, files):
    """True if this exact unproven set was already reported. Marks it if not."""
    if not session_id:
        return False
    key = hashlib.sha256(
        (str(session_id) + "\0" + "\0".join(files)).encode("utf-8")
    ).hexdigest()[:32]
    marker = Path(tempfile.gettempdir()) / "tte-unproven-gate" / key
    try:
        if marker.exists():
            return True
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("", encoding="utf-8")
    except OSError:
        return False  # can't dedupe; a repeated nudge beats a silent one
    return False


def message(files):
    """The reminder, or '' when there is nothing to say."""
    if not files:
        return ""
    shown = [Path(f).name for f in files[:4]]
    more = " (+%d more)" % (len(files) - 4) if len(files) > 4 else ""
    plural = "s" if len(files) != 1 else ""
    return (
        "[top-tier-engineer] %d source file%s changed with nothing run since: "
        "%s%s.\n"
        "Before claiming this works, either run the check that proves it, or "
        "label the claim plainly: proven (you ran it) / traced (you read the "
        "whole chain) / suspected (neither). Do not describe output you did "
        "not see." % (len(files), plural, ", ".join(shown), more)
    )


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0

    transcript = payload.get("transcript_path")
    if not transcript or not os.path.isfile(transcript):
        return 0

    files = unproven_files(_tail_lines(transcript))
    if not files or _already_warned(payload.get("session_id"), files):
        return 0

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError, OSError):
        pass
    print(message(files))
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        assert runs_something("pytest -q")
        assert runs_something("cat x.py && pytest")
        assert not runs_something("cat x.py")
        assert not runs_something("git status && grep foo bar")
        assert runs_something("git push")
        assert is_source("a/b.py") and not is_source("README.md")
        print("selftest ok")
        sys.exit(0)
    try:
        sys.exit(main())
    except BaseException:
        # Exit 2 here would erase the user's prompt. Never risk it.
        sys.exit(0)
