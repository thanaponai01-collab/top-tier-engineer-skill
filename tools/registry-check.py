#!/usr/bin/env python3
"""Reconcile PROTOCOL §5's verdict registry against verdict-lint.py's copy.

WHY THIS EXISTS
---------------
§5's noun -> state mapping is declared TWICE: once as the markdown table in
PROTOCOL.md (the doctrine, and the source of truth), and once as the REGISTRY
dict in tools/verdict-lint.py (what actually rejects a malformed verdict line).
Nothing checked that the two agreed. Add a state to doctrine and the linter
silently rejects a verdict the protocol permits; add one to the linter and
doctrine silently permits a verdict nobody declared. Either way the failure is
invisible, because both halves keep reporting green about themselves.

WHY THE LINTER DOES NOT JUST PARSE PROTOCOL.md AT RUNTIME
---------------------------------------------------------
verdict-lint.py runs inside CONSUMING repos, where PROTOCOL.md may live at an
unknown path, at a different vintage, or not be installed at all. A linter that
hard-depends on finding and parsing a markdown file at runtime fails open in
exactly those repos. So the tool keeps its own copy — and the drift between the
copies is checked HERE, in the suite's own enforcement floor, where PROTOCOL.md
is guaranteed present. Duplication with a mechanical reconciler; not duplication
on trust.

EXIT CODES
----------
  0  the two registries declare the same nouns and the same states
  1  drift: a noun or a state exists on one side only
  2  could not compare (file missing, table unparseable, no rows found) -- a
     hard error, never a silent pass. A reconciler that cannot find its inputs
     is the vacuous gate this check exists to prevent (PROTOCOL §12).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _encoding import utf8_streams

# A §5 table row:  | `NOUN` | owner | state \| state(qualifier) \| ... |
# The noun may carry a placeholder suffix (`SLICE <n>`, `MAINT <ID>`) which is
# part of the line grammar, not part of the noun.
ROW_RE = re.compile(r"^\|\s*`([A-Z][A-Z-]+)(?:\s+<[^>]+>)?`\s*\|([^|]*)\|\s*(.+?)\s*\|\s*$")

# The linter's dict literal:  "NOUN": {"state", "state"},
DICT_ENTRY_RE = re.compile(r'"([A-Z][A-Z-]+)":\s*\{([^}]*)\}')

PLACEHOLDER_RE = re.compile(r"^<.*>$")
STATE_RE = re.compile(r"^[a-z][a-z-]*$")


def parse_states(cell: str) -> set[str]:
    """Extract the legal state keywords from one §5 table cell.

    Alternatives are separated by an escaped pipe. Each alternative may carry a
    parenthesised qualifier (`pass(tag)`), a colon-introduced payload
    (`next: <skill>`), or be a pure placeholder (`<stage>`) standing for a
    free-form value rather than a fixed keyword. Only the leading keyword is a
    state; placeholders contribute nothing.
    """
    states: set[str] = set()
    for alt in cell.split(r"\|"):
        alt = alt.strip().strip("`").strip()
        if not alt or PLACEHOLDER_RE.match(alt):
            continue
        head = alt.split("(")[0].split(":")[0].strip()
        if STATE_RE.match(head):
            states.add(head)
    return states


def load_doctrine(path: Path) -> dict[str, set[str]]:
    """Read the §5 registry table out of PROTOCOL.md.

    Scoped to the §5 section so a table elsewhere in the document can never be
    mistaken for the registry.
    """
    text = path.read_text(encoding="utf-8")
    start = re.search(r"^## 5\.[^\n]*$", text, re.M)
    if not start:
        die(2, f"{path}: no '## 5.' section header — cannot locate the registry")
    rest = text[start.end():]
    end = re.search(r"^## \d+\.", rest, re.M)
    section = rest[: end.start()] if end else rest

    registry: dict[str, set[str]] = {}
    for line in section.splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        noun, _owner, states_cell = m.groups()
        states = parse_states(states_cell)
        if not states:
            die(2, f"{path}: §5 row for `{noun}` declares no parseable states")
        registry[noun] = states
    return registry


def load_tool(path: Path) -> dict[str, set[str]]:
    """Read the REGISTRY dict out of verdict-lint.py without importing it.

    Parsed as text rather than imported: importing would execute the module and
    couple this check to the linter's CLI, and a syntax error there should be
    reported by the linter's own tests, not swallowed here.
    """
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^REGISTRY = \{(.*?)^\}", text, re.S | re.M)
    if not m:
        die(2, f"{path}: no 'REGISTRY = {{...}}' block found")
    registry: dict[str, set[str]] = {}
    for noun, body in DICT_ENTRY_RE.findall(m.group(1)):
        states = {s.strip().strip('"') for s in body.split(",")}
        registry[noun] = {s for s in states if s}
    return registry


def compare(doc: dict[str, set[str]], tool: dict[str, set[str]]) -> list[str]:
    """Every way the two registries can disagree, phrased as its consequence."""
    problems: list[str] = []
    for noun in sorted(set(doc) - set(tool)):
        problems.append(
            f"  `{noun}` is registered in PROTOCOL §5 but the linter does not know it "
            f"— every {noun} verdict passes unchecked"
        )
    for noun in sorted(set(tool) - set(doc)):
        problems.append(
            f"  `{noun}` is enforced by the linter but has no §5 row "
            f"— an undeclared verdict noun"
        )
    for noun in sorted(set(doc) & set(tool)):
        missing = sorted(doc[noun] - tool[noun])
        extra = sorted(tool[noun] - doc[noun])
        if missing:
            problems.append(f"  `{noun}`: §5 permits {missing} but the linter rejects them")
        if extra:
            problems.append(
                f"  `{noun}`: the linter accepts {extra} but §5 does not declare them"
            )
    return problems


def die(code: int, msg: str) -> None:
    print(f"registry-check: {msg}", file=sys.stderr)
    raise SystemExit(code)


def main() -> int:
    utf8_streams()

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--protocol", default="PROTOCOL.md", type=Path)
    ap.add_argument("--linter", default="tools/verdict-lint.py", type=Path)
    args = ap.parse_args()

    for p in (args.protocol, args.linter):
        if not p.is_file():
            die(2, f"{p}: not found — cannot compare (this is a hard error, not a pass)")

    doc = load_doctrine(args.protocol)
    tool = load_tool(args.linter)

    if not doc:
        die(2, f"{args.protocol}: §5 registry table has no rows")
    if not tool:
        die(2, f"{args.linter}: REGISTRY is empty")

    problems = compare(doc, tool)

    nouns = len(set(doc) | set(tool))
    states = sum(len(v) for v in doc.values())

    if problems:
        print(f"registry-check: DRIFT between PROTOCOL §5 and {args.linter}")
        print("\n".join(problems))
        print(
            "\nPROTOCOL §5 is the source of truth. Fix the linter to match it, or amend "
            "§5 first and then the linter — never the linter alone."
        )
        print(f"REGISTRY: drift(nouns: {nouns}, findings: {len(problems)})")
        return 1

    print(
        f"registry-check: doctrine and linter agree — {nouns} nouns, "
        f"{states} states, no drift"
    )
    print(f"REGISTRY: clean(nouns: {nouns}, states: {states})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
