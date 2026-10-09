#!/usr/bin/env python3
"""context_budget.py — keep the files a fresh session reads short enough to be read.

A project's notes are read in three layers. The start-here block in CLAUDE.md or AGENTS.md is
loaded into every session. BRIEF.md and BUILD.md are read when work begins. Everything else
(FEATURES.md areas, WHY.md entries, every *.archive.md) is read only when a task needs it. A note
grows by sending old detail down a layer, never by getting longer at the top. This script says
which files broke their line budget and what to do about each; it changes nothing.

  start-here block   30 lines   between <!-- start-here --> and <!-- /start-here -->
  BRIEF.md          120 lines   and at most 25 entries under `## Decisions`
  BUILD.md           80 lines
  FEATURES.md       150 lines   each file it includes counts on its own
  VERIFY.md         150 lines   each file it includes counts on its own
  WHY.md            300 lines

*.archive.md files have no budget: they are read only by their own index line.

Usage:
  python scripts/context_budget.py [repo]

Exit: 0 = every file within budget, or none present; 1 = something over. Summary line:
  CONTEXT: <n> files | <o> over budget
Stdlib only.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams

START, END = "<!-- start-here -->", "<!-- /start-here -->"
BLOCK_BUDGET = 30
DECISIONS_BUDGET = 25
# name -> (line budget, the move that brings it back under, the skill that owns the file)
BUDGETS = {
    "BRIEF.md": (120, "retire decisions no longer in force to BRIEF.archive.md", "problem-framing"),
    "BUILD.md": (80, "archive proven, committed slices to BUILD.archive.md", "build-discipline"),
    "FEATURES.md": (150, "split by area: one `include: features/<area>.md` line per area", "feature-map"),
    "VERIFY.md": (150, "split by area: one `include: verify/<area>.md` line per area", "verify-loop"),
    "WHY.md": (300, "move old entries that still hold to WHY.archive.md", "code-history"),
}
INCLUDE = re.compile(r"^(?:[-*]\s+)?include:\s*`?([^`\s]+)`?", re.I)


def read(path):
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def line_count(text):
    return len(text.splitlines())


def includes(text):
    return [m.group(1).strip("'\"") for m in map(INCLUDE.match, (l.strip() for l in text.splitlines())) if m]


def start_block(text):
    """Lines strictly between the start-here markers, or None when there is no block."""
    if START not in text:
        return None
    body = text.split(START, 1)[1]
    return body.split(END, 1)[0] if END in body else body


def decisions(text):
    """Entries (list items) under a `## Decisions` heading."""
    m = re.search(r"(?ims)^##\s+decisions\s*$(.*?)(?=^##\s|\Z)", text)
    return [l for l in m.group(1).splitlines() if re.match(r"^\s*[-*]\s+\S", l)] if m else []


def measure(repo):
    """[{file, lines, budget, over, fix}] for every budgeted file present in `repo`."""
    rows = []

    def add(name, lines, budget, fix, owner):
        rows.append({"file": name, "lines": lines, "budget": budget, "over": lines > budget,
                     "fix": f"{fix} ({owner})"})

    for name in ("CLAUDE.md", "AGENTS.md"):
        text = read(os.path.join(repo, name))
        block = start_block(text) if text else None
        if block is not None:
            add(f"{name} start-here", line_count(block.strip("\n")), BLOCK_BUDGET,
                "keep the goal and links in the block; move detail to the files it links", "project-setup")

    for name, (budget, fix, owner) in BUDGETS.items():
        text = read(os.path.join(repo, name))
        if text is None:
            continue
        add(name, line_count(text), budget, fix, owner)
        if name == "BRIEF.md":
            entries = decisions(text)
            if entries:
                add("BRIEF.md decisions", len(entries), DECISIONS_BUDGET, fix, owner)
        seen = {os.path.normpath(os.path.join(repo, name))}
        queue = [(rel, budget, fix, owner) for rel in includes(text)]
        while queue:
            rel, budget, fix, owner = queue.pop(0)
            full = os.path.normpath(os.path.join(repo, rel))
            if full in seen:
                continue
            seen.add(full)
            sub = read(full)
            if sub is None:
                continue
            add(rel.replace("\\", "/"), line_count(sub), budget, "split this area further", owner)
            queue += [(r, budget, fix, owner) for r in includes(sub)]
    return rows


def render(rows):
    over = [r for r in rows if r["over"]]
    out = [f"CONTEXT: {len(rows)} files | {len(over)} over budget"]
    width = max((len(r["file"]) for r in rows), default=0)
    for r in sorted(rows, key=lambda r: not r["over"]):
        tag = "OVER" if r["over"] else "ok  "
        line = f"  {tag}  {r['file']:<{width}}  {r['lines']}/{r['budget']}"
        out.append(line + (f"  → {r['fix']}" if r["over"] else ""))
    return "\n".join(out)


def main(argv):
    utf8_streams()
    repo = argv[0] if argv else "."
    if not os.path.isdir(repo):
        print(f"no such directory: {repo}")
        return 2
    rows = measure(repo)
    if not rows:
        print("CONTEXT: no project notes to measure (no BRIEF.md, BUILD.md, FEATURES.md, VERIFY.md, WHY.md or start-here block)")
        return 0
    print(render(rows))
    return 1 if any(r["over"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
