#!/usr/bin/env python3
"""
spec_check.py — refuse a brief that does not fill work/SPEC_TEMPLATE.md.

    python tools/spec_check.py BRIEF.md [work/briefs/<skill>.md ...]

Exit 0 when every file passes, 1 with every problem listed otherwise.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECTIONS = [("Intent", ["Purpose", "End state", "Done when"]),
            ("Context", ["Grounding", "Scope", "Non-goals"]),
            ("Guardrails", ["Constraints", "Invariants", "Escalate"]),
            ("Freedom", ["Open choices"]),
            ("Gates", []),
            ("Output", ["Deliverable", "Acceptance", "Verification"])]
GATE_HEAD = ["Stage", "Precondition", "Postcondition", "Evidence"]
SLOT = re.compile(r"\[\[fill:")


def split_sections(text):
    """{name: body} for each `## N. Name` heading, plus the names in order."""
    found, order, cur = {}, [], None
    for line in text.splitlines():
        m = re.match(r"##\s+(?:\d+\.\s*)?(.+?)\s*$", line)
        if m and not line.startswith("###"):
            cur = m.group(1)
            order.append(cur)
            found[cur] = []
        elif cur is not None:
            found[cur].append(line)
    return {k: "\n".join(v) for k, v in found.items()}, order


def field(body, label):
    """Text of `- Label: ...` and the indented lines under it, or None when absent."""
    lines = body.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"-\s+(?:\*\*)?%s:?(?:\*\*)?:?\s*(.*)$" % re.escape(label), line)
        if m:
            parts = [m.group(1)]
            for nxt in lines[i + 1:]:
                if nxt.startswith((" ", "\t")) and nxt.strip():
                    parts.append(nxt.strip())
                else:
                    break
            return " ".join(p for p in parts if p).strip()
    return None


def gate_rows(body):
    rows = [[c.strip() for c in l.strip().strip("|").split("|")]
            for l in body.splitlines() if l.strip().startswith("|")]
    return rows


def check(path):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        return ["cannot read: %s" % e]
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    problems = []
    slots = SLOT.findall(re.sub(r"`[^`\n]*`", "", text))  # a slot quoted as code is prose
    if slots:
        problems.append("unfilled [[fill: ...]] slot: %d left" % len(slots))
    sections, order = split_sections(text)
    wanted = [name for name, _ in SECTIONS]
    present = [n for n in order if n in wanted]
    if present != [n for n in wanted if n in present]:
        problems.append("sections out of order: %s (want %s)"
                        % (", ".join(present), ", ".join(wanted)))
    for i, (name, labels) in enumerate(SECTIONS, 1):
        if name not in sections:
            problems.append("missing section: ## %d. %s" % (i, name))
            continue
        for label in labels:
            value = field(sections[name], label)
            if value is None:
                problems.append("%s: missing field '- %s:'" % (name, label))
            elif not value:
                problems.append("%s: empty field '%s'" % (name, label))
    if "Gates" in sections:
        rows = gate_rows(sections["Gates"])
        if not rows or rows[0] != GATE_HEAD:
            problems.append("Gates: want a table headed | %s |" % " | ".join(GATE_HEAD))
        else:
            body = [r for r in rows[1:] if not all(set(c) <= set("-: ") for c in r)]
            if not body:
                problems.append("Gates: no gate rows")
            for r in body:
                if len(r) != 4 or not all(r):
                    problems.append("Gates: row '%s' leaves a cell empty" % (r[0] if r else ""))
    if "Output" in sections:
        verification = field(sections["Output"], "Verification") or ""
        if verification and not re.search(r"`[^`]+`", verification):
            problems.append("Output: Verification names no `command`")
        for test in sorted(set(re.findall(r"tests/[\w/.-]+\.py", sections["Output"]))):
            if not os.path.exists(os.path.join(ROOT, test)):
                problems.append("Output: %s does not exist" % test)
        if not re.search(r"tests/[\w/.-]+\.py", sections["Output"]):
            problems.append("Output: Acceptance names no tests/*.py that holds it")
    return problems


def main(argv):
    if not argv:
        print(__doc__.strip())
        return 2
    bad = 0
    for path in argv:
        problems = check(path)
        if problems:
            bad += 1
            print("SPEC REFUSED %s" % path)
            for p in problems:
                print("  - %s" % p)
        else:
            print("SPEC OK %s" % path)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
