#!/usr/bin/env python3
"""
front-door — the one SessionStart hook a default install runs: what skills exist, where this project
stands, and whether the installed plugin is behind its source.

WHY THIS EXISTS
---------------
A fresh agent learns about skills from the host's skill listing, and that listing is a shared budget
(1% of the context window). Over budget, rarely used skills lose their description and can never
trigger by themselves, and manual-only skills are not listed at all. So the agent that most needs
`recall` or `project-setup` is the one that cannot see them. This prints the generated card
(CATALOG.md, one line per stage) once per session, which no listing budget can drop.

It fires once, at session start, never on a prompt: the 4.54 lesson was that skills firing on
ordinary work get a plugin uninstalled. Output stays small: the card is about 13 lines, the project
part is start-here-hook's summary (decisions in force, Next, notes over budget) or one setup line.

Fails open, always. Exit 2 on SessionStart prevents the session from starting, so every error path
exits 0, and a part that cannot be built is left out.

Usage:  SessionStart hook (payload on stdin; its `cwd` is the project)
        front-door.py --selftest [repo]
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
CATALOG = PLUGIN_ROOT / "CATALOG.md"
START_HERE_HOOK = PLUGIN_ROOT / "tools" / "start-here-hook.py"
PLUGIN = "top-tier-engineer"
INSTRUCTION_FILES = ("CLAUDE.md", "AGENTS.md", ".claude/CLAUDE.md")


def read(path):
    try:
        return Path(path).read_text(encoding="utf-8-sig", errors="replace")
    except (OSError, ValueError):
        return ""


def card():
    """The card body from CATALOG.md without its title and generator comment; '' if missing."""
    lines = [l for l in read(CATALOG).splitlines()
             if l.strip() and not l.startswith("# ") and not l.startswith("<!--")]
    return "\n".join(lines)


def project_summary(repo):
    """start-here-hook's summary for the repo; '' when it has nothing or cannot load."""
    try:
        spec = importlib.util.spec_from_file_location("start_here_hook", START_HERE_HOOK)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.summary(str(repo))
    except Exception:
        return ""


def has_start_here(repo):
    return any("<!-- start-here -->" in read(Path(repo) / f) for f in INSTRUCTION_FILES)


def setup_line(repo):
    """One line for a git project nobody has set up; '' elsewhere (home dir, scratch folders)."""
    repo = Path(repo)
    if not (repo / ".git").exists() or has_start_here(repo):
        return ""
    return (f"This project has no start-here block, so the next session starts cold. For work that "
            f"will span sessions, run /{PLUGIN}:project-setup once.")


def version_of(plugin_json):
    try:
        data = json.loads(read(plugin_json))
        return data.get("name"), tuple(int(p) for p in str(data.get("version", "")).split("."))
    except (ValueError, AttributeError):
        return None, ()


def freshness_line(repo):
    """When the session is in this plugin's own source checkout and it is ahead of what is installed."""
    repo = Path(repo)
    try:
        if repo.resolve() == PLUGIN_ROOT:
            return ""
    except OSError:
        return ""
    name, source = version_of(repo / ".claude-plugin" / "plugin.json")
    _, installed = version_of(PLUGIN_ROOT / ".claude-plugin" / "plugin.json")
    if name != PLUGIN or not source or not installed or source <= installed:
        return ""
    fmt = lambda v: ".".join(map(str, v))
    return (f"Installed {PLUGIN} is {fmt(installed)}; this checkout is {fmt(source)}. After pushing, "
            f"run /plugin marketplace update, then /plugin update {PLUGIN}, so sessions get it.")


def front_door(repo):
    parts = []
    c = card()
    if c:
        parts.append(c)
    summary = project_summary(repo)
    if summary:
        parts.append(summary)
    else:
        line = setup_line(repo)
        if line:
            parts.append(line)
    line = freshness_line(repo)
    if line:
        parts.append(line)
    return "\n\n".join(parts)


def emit(text):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError, OSError):
        pass
    print(text)


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (OSError, ValueError):
        payload = {}
    repo = payload.get("cwd") if isinstance(payload, dict) else None
    text = front_door(repo or os.getcwd())
    if text:
        emit(text)
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        args = [a for a in sys.argv[1:] if a != "--selftest"]
        emit(front_door(args[0] if args else os.getcwd()) or "front-door: nothing to show")
        sys.exit(0)
    try:
        sys.exit(main())
    except BaseException:
        sys.exit(0)
