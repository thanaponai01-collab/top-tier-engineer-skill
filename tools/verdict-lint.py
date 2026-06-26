#!/usr/bin/env python3
"""
verdict-lint — mechanical enforcement for the top-tier-engineer suite.

The suite is exhortation without enforcement (a known residual risk). This script
converts the *form* rules of PROTOCOL §5 into a check that needs no live-run data:
it reads a transcript / PR body / log on stdin or as a file argument and verifies
that the verdict lines present are well-formed and internally consistent.

It checks FORM, not correctness — it cannot know if a GATE:pass was deserved, but it
CAN catch a SLICE that closed trace-only without the required bold limitation marker,
an unknown verdict noun, or a malformed state. That is the cheapest enforcement
available and it requires nothing but the text.

Exit code 0 = clean, 1 = violations found. Usage:
    verdict-lint.py transcript.md
    cat transcript.md | verdict-lint.py
"""
import sys, re

# PROTOCOL §5 registry: noun -> set of legal state keywords (the word before any '(').
REGISTRY = {
    "LIFECYCLE":  {"next", "blocked"},                 # state is free-form stage; we check shape loosely
    "BRIEF":      {"ready", "blocked-on-questions", "revised"},
    "DESIGN":     {"ready", "blocked-on-director", "revised"},
    "SLICE":      {"proven", "trace-only", "failed"},
    "WIRE":       {"connected", "broken", "blocked"},
    "GATE":       {"pass", "fail"},
    "CAUSE":      {"proven", "trace-only", "unreproduced"},
    "AUDIT":      {"prescribed", "clean", "rerouted", "blocked"},
    "OPTIMIZE":   {"budgets-met", "improved", "stopped", "reverted"},
    "DATATIER":   {"clean", "findings", "blocked"},
    "REVIEW":     {"shippable", "shippable-with-findings", "not-shippable"},
    "SCRUTINY":   {"ship", "fix-then-ship", "rework", "reject", "blocked"},
    "STRUCTURE":  {"clean", "findings", "blocked"},
    "MAINT":      {"resolved", "escalated", "reverted"},
    # v1.5.0 additions:
    "THREAT":     {"clear", "findings", "blocked"},
    "SHIP":       {"go", "stage", "hold", "escalated"},
    "MIGRATE":    {"planned", "verified", "blocked"},
    # v1.9.0: tool-output noun — emitted by run-trace.py, not owned by any skill
    "TRACE":      {"complete", "incomplete", "blocked"},
}

# A verdict line: NOUN[ <name>]: state[(qualifier)] [| state...]
# May be wrapped in backticks/bold in a markdown report, so strip leading `* and whitespace.
# The optional `(?:\s+[^:]+?)?` segment matches the `<name>`/`<ID>` that SLICE and MAINT carry
# (e.g. `SLICE login:`, `MAINT BUG-12:`) — the same allowance PROTOCOL §5's recovery grep needs.
NOUN_RE = re.compile(r'^[\s`*>]*([A-Z][A-Z-]+)(?:\s+[^:]+?)?:\s*(.+)$')


def lint(text: str):
    violations = []
    lines = text.splitlines()
    seen_nouns = set()
    noun_events = []  # (line_no, noun, first_state) — for sequence validation (Gap 2c)

    for i, raw in enumerate(lines, 1):
        m = NOUN_RE.match(raw)
        if not m:
            continue
        noun, rest = m.group(1), m.group(2).strip().rstrip('`*')
        if noun not in REGISTRY:
            # Not a suite verdict noun — prose like "REVERSIBLE: True" in a code block.
            # We deliberately do NOT warn here: only registered nouns are linted, because
            # any-caps-word-colon generates more false positives than signal.
            continue
        seen_nouns.add(noun)

        # First state keyword = text up to first '(' or '|' or whitespace.
        first_state = re.split(r'[(\s|]', rest, maxsplit=1)[0]
        legal = REGISTRY[noun]
        # Gap 2a fix: only LIFECYCLE is exempt (truly free-form stage labels).
        # SLICE (proven|trace-only|failed) and MAINT (resolved|escalated|reverted) have
        # defined states and must be validated.
        if noun not in {"LIFECYCLE"} and first_state not in legal:
            violations.append((i, noun, f"state '{first_state}' not legal for {noun}; expected one of {sorted(legal)}"))

        # Evidence-marker rule: a trace-only close must carry a paragraph-level bold limitation
        # statement nearby (PROTOCOL §1). Gap 2b fix: require a line starting with '**' within
        # 8 lines (paragraph-level bold, not incidental inline bold).
        if "trace-only" in rest:
            window_lines = lines[max(0, i-8):i]
            if not any(re.match(r'^\s*\*\*', l) for l in window_lines):
                violations.append((i, noun,
                    "trace-only verdict without a paragraph-level bold limitation marker "
                    "(a line beginning '**...') within the preceding 8 lines "
                    "(PROTOCOL §1: state the execution limitation in bold)"))

        # Contradiction: a success state on the same line as a failure state — but only WITHIN
        # the first alternative. Grammar lines list all states separated by '|' (e.g.
        # 'go(...) | hold(...)'); those are alternatives, not a contradiction. Check only the
        # text up to the first '|'.
        first_alt = rest.split('|')[0]
        SUCCESS = {"pass", "proven", "ship", "go", "clear", "shippable", "ready",
                   "connected", "resolved", "budgets-met", "improved", "verified",
                   "planned", "clean"}
        FAILURE_RE = re.compile(r'\b(fail|failed|broken|reject|not-shippable|unreproduced|hold|reverted)\b')
        if first_state in SUCCESS and FAILURE_RE.search(first_alt):
            # 'shippable-with-findings' legitimately pairs success+findings; exclude that compound.
            if first_state != "shippable" or "with-findings" not in first_alt:
                violations.append((i, noun, f"{noun} claims '{first_state}' but the same verdict names a failure state"))

        noun_events.append((i, noun, first_state))

    # Gap 2c: sequence validation — check §4 handoff chain ordering across the full transcript.
    violations.extend(_check_sequence(noun_events))

    return violations, seen_nouns


def _check_sequence(noun_events):
    """Validate that verdict ordering follows the §4 handoff chain.

    Checks three invariants that are individually valid verdicts but collectively impossible
    if sequencing is violated:
      - GATE: pass must have a preceding SLICE: proven (build-discipline before correctness-gate)
      - SHIP: go|stage must have a preceding GATE: pass (correctness-gate before ship-gate)
      - MIGRATE must have a preceding SHIP or MAINT (data-evolution is invoked by ship-gate or evolve-maintain)
    """
    violations = []
    for idx, (line_no, noun, first_state) in enumerate(noun_events):
        preceding = noun_events[:idx]

        if noun == "GATE" and first_state == "pass":
            if not any(n == "SLICE" and s == "proven" for _, n, s in preceding):
                violations.append((line_no, "GATE",
                    "pass verdict with no preceding SLICE: proven in this transcript "
                    "(§4: correctness-gate consumes build-discipline's proven slices)"))

        if noun == "SHIP" and first_state in {"go", "stage"}:
            if not any(n == "GATE" and s == "pass" for _, n, s in preceding):
                violations.append((line_no, "SHIP",
                    "go/stage verdict with no preceding GATE: pass in this transcript "
                    "(§4: ship-gate requires a passed correctness-gate)"))

        if noun == "MIGRATE":
            has_ship = any(n == "SHIP" for _, n, s in preceding)
            has_maint = any(n == "MAINT" for _, n, s in preceding)
            if not has_ship and not has_maint:
                violations.append((line_no, "MIGRATE",
                    "verdict with no preceding SHIP or MAINT in this transcript "
                    "(§4: data-evolution is invoked by ship-gate or evolve-maintain)"))

    return violations


def main():
    if len(sys.argv) > 1:
        # utf-8-sig so a transcript saved with a BOM (common on Windows editors) still lints —
        # without it a leading ﻿ hides the first verdict line and the gate passes vacuously.
        with open(sys.argv[1], encoding="utf-8-sig") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    violations, seen = lint(text)

    if not seen:
        print("verdict-lint: no verdict lines found. "
              "(A completed suite run should end each skill with one — PROTOCOL §5.)")
        # Absence of verdict lines is a soft warning, not a hard failure.
        return 0

    if not violations:
        print(f"verdict-lint: clean — {len(seen)} verdict noun(s) present "
              f"({', '.join(sorted(seen))}), all well-formed.")
        return 0

    print(f"verdict-lint: {len(violations)} violation(s):\n")
    for line_no, noun, msg in violations:
        print(f"  line {line_no} [{noun}]: {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
