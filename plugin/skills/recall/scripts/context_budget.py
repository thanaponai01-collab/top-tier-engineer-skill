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
  python scripts/context_budget.py [repo] [--check-handoff]

Exit: 0 = every file within budget (legacy mode allows no notes); 1 = over budget or,
with --check-handoff, structural gaps. Equivalent intent/work documents are selected by
`intent:` and `work:` lines in start-here. This checks structure, not fidelity to owner intent.
Summary line:
  CONTEXT: <n> files | <o> over budget
Stdlib only.
"""
import argparse, os, re, sys
from urllib.parse import unquote, urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams

START, END = "<!-- start-here -->", "<!-- /start-here -->"
BLOCK_BUDGET = 30
DECISIONS_BUDGET = 25
# name -> (line budget, the move that brings it back under, the skill that owns the file)
BUDGETS = {
    "BRIEF.md": (120, "archive superseded decisions to BRIEF.archive.md; split active area decisions via include: brief/<area>.md", "problem-framing"),
    "BUILD.md": (80, "archive completed proof to BUILD.archive.md; split unfinished areas via include: work/<area>.md, retaining Next and blockers", "build-discipline"),
    "FEATURES.md": (150, "split by area: one `include: features/<area>.md` line per area", "feature-map"),
    "VERIFY.md": (150, "split by area: one `include: verify/<area>.md` line per area", "verify-loop"),
    "WHY.md": (300, "move old entries that still hold to WHY.archive.md", "code-history"),
}
INCLUDE = re.compile(r"^(?:[-*]\s+)?include:\s*`?([^`\s]+)`?", re.I)
ROLE = re.compile(r"^\s*(?:[-*]\s+)?(intent|work):\s*`?([^`\s]+)`?", re.I | re.M)
LINK = re.compile(r"\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)")


def roles(repo):
    selected = {"intent": "BRIEF.md", "work": "BUILD.md"}
    for name in ("AGENTS.md", "CLAUDE.md"):
        block = start_block(read(os.path.join(repo, name)) or "")
        if block is not None:
            selected.update({m.group(1).lower(): m.group(2) for m in ROLE.finditer(block)})
    return selected


def handoff_issues(repo):
    """Structural completeness only; a passing result cannot establish requirement quality."""
    issues, blocks = [], []
    base = os.path.realpath(repo)
    for name in ("AGENTS.md", "CLAUDE.md"):
        text = read(os.path.join(repo, name)) or ""
        if START in text or END in text:
            if text.count(START) != 1 or text.count(END) != 1 or text.find(END) < text.find(START):
                issues.append(f"{name}: start-here markers must form one complete block")
            else:
                blocks.append(start_block(text))
    if not blocks:
        issues.append("missing start-here block in AGENTS.md or CLAUDE.md")
    selected = roles(repo)
    declared = {}
    for block in blocks:
        for m in ROLE.finditer(block):
            role, target = m.group(1).lower(), m.group(2)
            if role in declared and declared[role] != target:
                issues.append(f"conflicting {role} pointers: {declared[role]} and {target}")
            declared[role] = target

    def local_path(rel, origin):
        rel = rel.replace("\\", "/")
        full = os.path.realpath(os.path.join(base, rel))
        try:
            inside = os.path.commonpath([base, full]) == base
        except ValueError:
            inside = False
        if not inside:
            issues.append(f"{origin}: context link outside project: {rel}")
            return None
        if not os.path.isfile(full):
            issues.append(f"{origin}: missing context file {rel}")
            return None
        return full

    queue = []
    for role, rel in selected.items():
        full = local_path(rel, role)
        if blocks and not any(rel in block for block in blocks):
            issues.append(f"start-here: link {role} document {rel}")
        if full is None:
            continue
        text = read(full) or ""
        content = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith(("#", "<!--"))]
        if not content:
            issues.append(f"{rel}: empty {role} document")
        if role == "work":
            nxt = re.search(r"(?ims)^##\s+Next\s*$(.*?)(?=^##\s|\Z)", text)
            if not nxt or not nxt.group(1).strip():
                issues.append(f"{rel}: missing or empty ## Next")
        queue.append(full)
    for name in BUDGETS:
        full = os.path.join(base, name)
        if os.path.isfile(full):
            queue.append(full)
    for block in blocks:
        for match in LINK.finditer(block):
            target = match.group(1) or match.group(2)
            if not urlsplit(target).scheme and not target.startswith("#"):
                full = local_path(unquote(urlsplit(target).path), "start-here")
                if full and full.lower().endswith(".md"):
                    queue.append(full)
    seen = set()
    while queue:
        full = queue.pop(0)
        if full in seen:
            continue
        seen.add(full)
        text = read(full) or ""
        targets = [(rel, base) for rel in includes(text)]
        targets += [((m.group(1) or m.group(2)), os.path.dirname(full)) for m in LINK.finditer(text)]
        for target, parent in targets:
            url = urlsplit(target)
            if url.scheme or target.startswith("#"):
                continue
            rel = os.path.relpath(os.path.join(parent, unquote(url.path)), base)
            linked = local_path(rel, os.path.relpath(full, base))
            if linked and linked.lower().endswith(".md") and not linked.lower().endswith(".archive.md"):
                queue.append(linked)
    return list(dict.fromkeys(issues))


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

    selected = roles(repo)
    for canonical, (budget, fix, owner) in BUDGETS.items():
        name = selected["intent"] if canonical == "BRIEF.md" else selected["work"] if canonical == "BUILD.md" else canonical
        text = read(os.path.join(repo, name))
        if text is None:
            continue
        add(name, line_count(text), budget, fix, owner)
        if canonical == "BRIEF.md":
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
            if canonical == "BRIEF.md" and decisions(sub):
                add(rel.replace("\\", "/") + " decisions", len(decisions(sub)), DECISIONS_BUDGET,
                    "split active decisions by area; archive only superseded decisions", owner)
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
    parser = argparse.ArgumentParser(description="Check context sizes and optionally handoff structure.")
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--check-handoff", action="store_true")
    args = parser.parse_args(argv)
    repo = args.repo
    if not os.path.isdir(repo):
        print(f"no such directory: {repo}")
        return 2
    rows = measure(repo)
    issues = handoff_issues(repo) if args.check_handoff else []
    if not rows:
        print("CONTEXT: no project notes to measure (no BRIEF.md, BUILD.md, FEATURES.md, VERIFY.md, WHY.md or start-here block)")
    else:
        print(render(rows))
    if args.check_handoff:
        print(f"HANDOFF: {len(issues)} structural gaps")
        for issue in issues:
            print(f"  GAP  {issue}")
    return 1 if issues or any(r["over"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
