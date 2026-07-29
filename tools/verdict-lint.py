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
    # v1.15.0: `held`/`regressed` are the ratchet states — a run measured against an
    # accepted structural baseline. `held` means known debt did not grow; `regressed`
    # means a NEW breach appeared or an accepted one got worse (PROTOCOL §10).
    "STRUCTURE":  {"clean", "findings", "blocked", "held", "regressed"},
    "LATENT":     {"clean", "findings", "blocked"},
    "MAINT":      {"resolved", "escalated", "reverted"},
    # v1.5.0 additions:
    "THREAT":     {"clear", "findings", "blocked"},
    "SHIP":       {"go", "stage", "hold", "escalated"},
    "MIGRATE":    {"planned", "verified", "blocked"},
    # v1.9.0: tool-output noun — emitted by run-trace.py, not owned by any skill
    "TRACE":      {"complete", "incomplete", "blocked"},
    # v1.13.0: shared noun (PROTOCOL §9) — emitted by whichever skill delivers a Law-5 fix.
    # coherent/incoherent require a SCRUTINY verdict in the same transcript (a delivered fix
    # is a delta); unscrutinized is the honest weak close and carries the same bold
    # limitation marker a trace-only close carries. Both rules enforced below.
    "FIX":        {"coherent", "incoherent", "unscrutinized"},
}

# A verdict line: NOUN[ <name>]: state[(qualifier)] [| state...]
# May be wrapped in backticks/bold in a markdown report, so strip leading `* and whitespace.
# The optional `(?:\s+[^:]+?)?` segment matches the `<name>`/`<ID>` that SLICE and MAINT carry
# (e.g. `SLICE login:`, `MAINT BUG-12:`) — the same allowance PROTOCOL §5's recovery grep needs.
NOUN_RE = re.compile(r'^[\s`*>]*([A-Z][A-Z-]+)(?:\s+[^:]+?)?:\s*(.+)$')


# Contradiction check vocabulary (module-level so _lint_verdict_line stays cheap).
SUCCESS = {"pass", "proven", "ship", "go", "clear", "shippable", "ready",
           "connected", "resolved", "budgets-met", "improved", "verified",
           "planned", "clean", "held"}
FAILURE_RE = re.compile(r'\b(fail|failed|broken|reject|not-shippable|unreproduced|hold|reverted)\b')


def _missing_bold_marker(lines, i):
    """True when no paragraph-level bold line ('**...') exists in the 8 lines above line i.

    This marker rule serves two honest-weak closes: a trace-only verdict (PROTOCOL §1) and a
    FIX closed 'unscrutinized' (PROTOCOL §9) — same window, same shape (Gap 2b fix)."""
    window_lines = lines[max(0, i - 8):i]
    return not any(re.match(r'^\s*\*\*', l) for l in window_lines)


def _lint_verdict_line(i, noun, rest, first_state, lines):
    """All single-line checks for one verdict line; returns that line's violations."""
    violations = []
    legal = REGISTRY[noun]
    # Gap 2a fix: only LIFECYCLE is exempt (truly free-form stage labels).
    # SLICE (proven|trace-only|failed) and MAINT (resolved|escalated|reverted) have
    # defined states and must be validated.
    if noun not in {"LIFECYCLE"} and first_state not in legal:
        violations.append((i, noun, f"state '{first_state}' not legal for {noun}; expected one of {sorted(legal)}"))

    # Evidence-marker rule: a trace-only close must carry a paragraph-level bold limitation
    # statement nearby (PROTOCOL §1).
    if "trace-only" in rest and _missing_bold_marker(lines, i):
        violations.append((i, noun,
            "trace-only verdict without a paragraph-level bold limitation marker "
            "(a line beginning '**...') within the preceding 8 lines "
            "(PROTOCOL §1: state the execution limitation in bold)"))

    # PROTOCOL §9: an unscrutinized fix is the FIX-noun analogue of trace-only — an honest
    # weak close that must carry the same paragraph-level bold limitation marker.
    if noun == "FIX" and first_state == "unscrutinized" and _missing_bold_marker(lines, i):
        violations.append((i, noun,
            "FIX closed 'unscrutinized' without a paragraph-level bold limitation "
            "marker (a line beginning '**...') within the preceding 8 lines "
            "(PROTOCOL §9: the honest weak close states its limitation in bold)"))

    # Contradiction: a success state on the same line as a failure state — but only WITHIN
    # the first alternative. Grammar lines list all states separated by '|' (e.g.
    # 'go(...) | hold(...)'); those are alternatives, not a contradiction.
    first_alt = rest.split('|')[0]
    if first_state in SUCCESS and FAILURE_RE.search(first_alt):
        # 'shippable-with-findings' legitimately pairs success+findings; exclude that compound.
        if first_state != "shippable" or "with-findings" not in first_alt:
            violations.append((i, noun, f"{noun} claims '{first_state}' but the same verdict names a failure state"))

    return violations


def _check_fix_scrutiny(noun_events, seen_nouns):
    """PROTOCOL §9: a delivered fix is a delta. A FIX line claiming adjudication
    (coherent/incoherent) without any SCRUTINY verdict in the transcript is the exact
    failure AUDIT_001 found in LIVE_RUN_004 — a fix waved past the outsider pass."""
    if "SCRUTINY" in seen_nouns:
        return []
    return [(ln, noun,
             f"FIX claims '{state}' but no SCRUTINY verdict exists in this transcript "
             "— a delivered fix is a delta and must be adjudicated by scrutinize "
             "(PROTOCOL §9), or the FIX line must honestly close 'unscrutinized'")
            for ln, noun, state in noun_events
            if noun == "FIX" and state in {"coherent", "incoherent"}]


# PROTOCOL §11 (the sense floor): a director-facing report opens with the DELIVERY block.
# Fields may be bold, quoted, list-item'd, or heading'd in a markdown report.
DELIVERY_RE = re.compile(r'^[\s`*>#|+-]*\*{0,2}(ASKED|DID|SO|COST)\*{0,2}\s*:', re.M)
# ASKED must QUOTE the director; the paraphrase is exactly the drift §11 exists to catch.
ASKED_RE = re.compile(r'^[\s`*>#|+-]*\*{0,2}ASKED\*{0,2}\s*:\s*(.+)$', re.M)
QUOTE_CHARS = '"“”‘’\'`'
# A rule may not condemn an artifact written before it existed. A transcript states which
# PROTOCOL version judged it (`PROTOCOL: 1.15.0`); checks younger than that declaration are
# skipped for that file. The pin rule (§1) applied to the rules themselves — general, so the
# next added check reuses it instead of re-litigating its own history.
PROTOCOL_DECL_RE = re.compile(r'^[\s`*>#|+-]*\*{0,2}PROTOCOL\*{0,2}\s*:\s*v?(\d+)\.(\d+)', re.M)
SENSE_FLOOR_SINCE = (1, 16)


def _declared_protocol(text):
    m = PROTOCOL_DECL_RE.search(text)
    return (int(m.group(1)), int(m.group(2))) if m else None


def _check_delivery_block(text, seen_nouns, noun_events):
    """PROTOCOL §11: fit, proportion and legibility have no gate unless the DELIVERY
    block is mechanically required — §8.1 prefers a structural check over a marker.

    Scope guard: this fires only on DIRECTOR-FACING reports, identified as a LIFECYCLE
    line (chief-engineer owns the one report) or two-plus distinct verdict nouns (a
    multi-stage run). An isolated §8.2 gate agent emits one noun and reports to the
    merging skill, not to the director — requiring a DELIVERY block there would wedge
    exactly the parallel gates §8.2 exists to enable.
    """
    if "LIFECYCLE" not in seen_nouns and len(seen_nouns) < 2:
        return []
    declared = _declared_protocol(text)
    if declared is not None and declared < SENSE_FLOOR_SINCE:
        return []  # judged by the rules it was written under
    at = noun_events[0][0] if noun_events else 1
    present = {m.group(1) for m in DELIVERY_RE.finditer(text)}
    missing = [f for f in ("ASKED", "DID", "SO", "COST") if f not in present]
    if missing:
        return [(at, "DELIVERY",
                 f"director-facing report is missing DELIVERY field(s) {', '.join(missing)} "
                 "— PROTOCOL §11 requires ASKED/DID/SO/COST before any verdict, so the run "
                 "is checkable against the request that started it, not only against the "
                 "criteria derived from it")]
    m = ASKED_RE.search(text)
    if m and not any(c in m.group(1) for c in QUOTE_CHARS):
        return [(at, "DELIVERY",
                 "ASKED does not quote the director's own words (PROTOCOL §11: the "
                 "paraphrase is the drift — quote the request, never summarize it)")]
    return []


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
        # §9 grammar precision: a FIX verdict is `FIX <id>:` where <id> is a bare token.
        # Prose like "FIX (single batched IN-clause): ..." is not a verdict line — the loose
        # NOUN_RE name segment would swallow the parenthetical, so re-check the strict shape
        # here and skip non-conforming lines as prose (regression: LIVE_RUN_002 line 75).
        if noun == "FIX" and not re.match(r'^[\s`*>]*FIX(?:\s+[A-Za-z0-9._-]+)?:', raw):
            continue
        if noun not in REGISTRY:
            # Not a suite verdict noun — prose like "REVERSIBLE: True" in a code block.
            # We deliberately do NOT warn here: only registered nouns are linted, because
            # any-caps-word-colon generates more false positives than signal.
            continue
        seen_nouns.add(noun)

        # First state keyword = text up to first '(' or '|' or whitespace.
        first_state = re.split(r'[(\s|]', rest, maxsplit=1)[0]
        violations.extend(_lint_verdict_line(i, noun, rest, first_state, lines))
        noun_events.append((i, noun, first_state))

    # Gap 2c: sequence validation — check §4 handoff chain ordering across the full transcript.
    violations.extend(_check_sequence(noun_events))
    # PROTOCOL §9: FIX adjudication requires a SCRUTINY verdict in the same transcript.
    violations.extend(_check_fix_scrutiny(noun_events, seen_nouns))
    # PROTOCOL §11: a director-facing report opens with the DELIVERY block.
    violations.extend(_check_delivery_block(text, seen_nouns, noun_events))

    return violations, seen_nouns


def _had(preceding, noun, state=None):
    # ponytail: extracts the `and` from generators so _check_sequence stays under the complexity limit
    return any(n == noun and (state is None or s == state) for _, n, s in preceding)


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
            if not _had(preceding, "SLICE", "proven"):
                violations.append((line_no, "GATE",
                    "pass verdict with no preceding SLICE: proven in this transcript "
                    "(§4: correctness-gate consumes build-discipline's proven slices)"))

        if noun == "SHIP" and first_state in {"go", "stage"}:
            if not _had(preceding, "GATE", "pass"):
                violations.append((line_no, "SHIP",
                    "go/stage verdict with no preceding GATE: pass in this transcript "
                    "(§4: ship-gate requires a passed correctness-gate)"))

        if noun == "MIGRATE":
            if not _had(preceding, "SHIP") and not _had(preceding, "MAINT"):
                violations.append((line_no, "MIGRATE",
                    "verdict with no preceding SHIP or MAINT in this transcript "
                    "(§4: data-evolution is invoked by ship-gate or evolve-maintain)"))

    return violations


def release_check(root):
    """Every surface that states the release version must state the SAME one.

    This drift shipped twice (v1.7.1 router, v1.9.2→1.10.0 manifest) — cheaper to check
    than to remember. v1.16.1: the check covered plugin.json and CHANGELOG.md but not
    `.claude-plugin/marketplace.json`, which carries its own `version` per plugin entry.
    v1.16.0 updated the two covered surfaces and left marketplace.json at 1.15.0; the
    gate reported "release clean" while a third surface disagreed. A drift check that
    knows about some of the surfaces is a drift check with a blind spot, and the blind
    spot is where the drift goes."""
    import json
    from pathlib import Path
    root = Path(root)
    try:
        manifest = json.loads((root / ".claude-plugin" / "plugin.json")
                              .read_text(encoding="utf-8-sig"))["version"]
        changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8-sig")
    except (OSError, KeyError, ValueError):
        return None  # not a plugin repo — nothing to check
    m = re.search(r'^##\s+(\S+)', changelog, re.M)
    if not m:
        return "CHANGELOG.md has no '## <version>' heading"
    if m.group(1) != manifest:
        return f"version drift: plugin.json says {manifest}, CHANGELOG top entry is {m.group(1)}"

    # marketplace.json is optional (a plugin repo need not publish one), but when it
    # lists THIS plugin it must agree. Keyed on the manifest's own name, never on a
    # directory name or list position.
    try:
        mkt = json.loads((root / ".claude-plugin" / "marketplace.json")
                         .read_text(encoding="utf-8-sig"))
        me = json.loads((root / ".claude-plugin" / "plugin.json")
                        .read_text(encoding="utf-8-sig"))["name"]
    except (OSError, KeyError, ValueError):
        return None  # no marketplace, or it is unreadable — nothing further to check
    for entry in mkt.get("plugins", []):
        if entry.get("name") == me and "version" in entry:
            if entry["version"] != manifest:
                return (f"version drift: plugin.json says {manifest}, "
                        f"marketplace.json entry '{me}' says {entry['version']}")
    return None


def main():
    # Output carries non-ASCII (the § section mark). On Windows a redirected pipe
    # defaults to cp1252, so emit valid UTF-8 like run-trace.py / structure-report.py
    # do — otherwise any UTF-8 consumer (or CI) chokes on the byte.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if "--help" in sys.argv or "-h" in sys.argv:
        print("verdict-lint — check PROTOCOL §5 verdict-line FORM (not merit),\n"
              "plus the §11 DELIVERY block on director-facing reports.\n"
              "  verdict-lint.py <transcript>   lint a file\n"
              "  verdict-lint.py                lint stdin\n"
              "  verdict-lint.py --release [root]   check plugin.json vs CHANGELOG\n"
              "                                    vs marketplace.json\n"
              "Exit: 0 clean, 1 violations.")
        return 0

    if "--release" in sys.argv:
        i = sys.argv.index("--release")
        root = sys.argv[i + 1] if len(sys.argv) > i + 1 else "."
        err = release_check(root)
        if err:
            print(f"verdict-lint: {err}")
            return 1
        print("verdict-lint: release clean — every surface that states a version agrees "
              "(plugin.json, CHANGELOG.md, marketplace.json where present).")
        return 0

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
