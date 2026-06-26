#!/usr/bin/env python3
"""
run-trace — "did it actually build?" — the run-completeness instrument.

WHY THIS EXISTS
---------------
The suite's skills are contracts the agent READS, not code that runs. So a director
who cannot read code has no way to see whether a run actually executed the stages it
should have, or merely claimed to. The agent's prose report says "done"; nothing
shows which skills truly engaged. The verdict lines (SLICE/WIRE/GATE/...) ARE that
trace — every skill ends with one — but nobody collects them into one readable view,
and verdict-lint.py checks only that the lines present are well-FORMED, not that the
RIGHT ONES are present for the kind of work requested.

This tool closes that. It reads a completed run's transcript, infers what KIND of
request it was, and reports — in plain language a non-coder can act on — whether the
verdicts expected for that kind of work actually appeared, in the right order. It
turns "I have no idea if it built" into a readable yes / no / partial.

RELATIONSHIP TO verdict-lint.py (Law 1 — one owner per rule)
------------------------------------------------------------
  verdict-lint.py : is each verdict line well-FORMED, and is the ordering legal?
                    (FORM + ORDERING — already owned there, not duplicated here)
  run-trace.py    : for THIS request type, are the EXPECTED verdicts all PRESENT?
                    (COMPLETENESS — the new owner)
run-trace calls nothing in verdict-lint; it parses verdicts independently for its own
purpose. Run both: verdict-lint says "the lines are valid," run-trace says "the run
is complete."

WHAT IT CANNOT DO (honesty — evidence discipline)
-------------------------------------------------
It checks that a verdict was REPORTED, not that the work behind it was real. A
fabricated `GATE: pass` passes this tool. Completeness is a necessary, not
sufficient, signal: a MISSING expected verdict is (proven) evidence a stage was
skipped; a PRESENT one is only (trace-only) evidence the stage ran — the verdict
could be hollow. The tool says exactly this in its output and never overclaims. The
deeper "was the GATE deserved" question is correctness-gate's and senior-review's,
never this tool's.

VERDICT LINE (PROTOCOL §5)
-------------------------
    TRACE: complete(<request-type>: all N expected stages present)
    TRACE: incomplete(<request-type>: missing <stage(s)>) | review-needed
    TRACE: blocked(no verdict lines found — run produced no trace)

EXIT CODES
----------
  0 = complete (every expected verdict for the inferred request type is present)
  1 = incomplete (one or more expected verdicts missing) — review-needed
  2 = blocked (no verdict lines at all — nothing to trace)

USAGE
-----
    run-trace.py transcript.md
    cat transcript.md | run-trace.py
    run-trace.py transcript.md --expect build   # force a request type, skip inference
    run-trace.py transcript.md --json
"""
import sys
import re
import json
import argparse

# Verdict-line parser — same shape rule as verdict-lint.py's NOUN_RE, kept local so
# this tool stands alone. (The shape rule is PROTOCOL §5's, stated there; this is a
# reader of that grammar, not a second definition of it.)
NOUN_RE = re.compile(r'^[\s`*>]*([A-Z][A-Z-]+)(?:\s+[^:]+?)?:\s*(.+)$')

KNOWN_NOUNS = {
    "LIFECYCLE", "BRIEF", "DESIGN", "SLICE", "WIRE", "GATE", "CAUSE", "AUDIT",
    "OPTIMIZE", "DATATIER", "REVIEW", "SCRUTINY", "MAINT", "THREAT", "SHIP",
    "MIGRATE", "STRUCTURE",
}

# ---- Request-type profiles --------------------------------------------------------
# Each profile says: for this kind of request, which verdict nouns MUST appear for the
# run to be complete, and which are expected-but-optional (present only if conditions
# held). Derived from the PROTOCOL §4 handoff chain — the canonical source. If §4
# changes, these profiles change with it (they are a downstream reading of it).
#
# "required"   : absence is a (proven) skipped-stage finding.
# "conditional": absence is fine; presence is noted. (e.g. WIRE only if a slice built;
#                MIGRATE only if a schema changed.)
PROFILES = {
    "build": {
        "label": "Build a feature / implement something",
        "required": ["SLICE", "GATE"],
        "conditional": ["WIRE", "REVIEW", "STRUCTURE", "SHIP", "MIGRATE"],
        "plain_missing": {
            "SLICE": "no slice was ever proven — the build either didn't happen or wasn't reported as built",
            "WIRE": "nothing confirms the new code is wired into the running system (it may be dead code)",
            "GATE": "correctness was never gated — nothing proves it actually works, only that it was written",
        },
    },
    "fix": {
        "label": "Fix a bug",
        "required": ["CAUSE", "MAINT"],
        "conditional": ["SLICE", "GATE", "WIRE"],
        "plain_missing": {
            "CAUSE": "the root cause was never proven — a fix without a proven cause is a guess",
            "MAINT": "the fix was never recorded as resolved — the loop wasn't closed",
        },
    },
    "review": {
        "label": "Review / audit code quality",
        "required": ["REVIEW"],
        "conditional": ["STRUCTURE", "THREAT"],
        "plain_missing": {
            "REVIEW": "no review verdict — the review didn't conclude with a shippable / not-shippable call",
        },
    },
    "scrutinize": {
        "label": "Scrutinize a change / PR / plan before it lands",
        "required": ["SCRUTINY"],
        "conditional": ["STRUCTURE"],
        "plain_missing": {
            "SCRUTINY": "no scrutiny verdict — the change was never actually adjudicated",
        },
    },
    "ship": {
        "label": "Ship / release",
        "required": ["GATE", "SHIP"],
        "conditional": ["THREAT", "MIGRATE", "REVIEW", "STRUCTURE"],
        "plain_missing": {
            "GATE": "shipping without a correctness gate — nothing proves what's shipping works",
            "SHIP": "no ship verdict — the release decision (go / hold) was never recorded",
        },
    },
    "perf": {
        "label": "Make it faster / optimize",
        "required": ["OPTIMIZE"],
        "conditional": ["DATATIER", "GATE"],
        "plain_missing": {
            "OPTIMIZE": "no optimize verdict — nothing records whether the budget was met or work stopped",
        },
    },
    "audit": {
        "label": "Audit an existing codebase for a felt symptom",
        "required": ["AUDIT"],
        "conditional": ["SLICE", "GATE", "CAUSE", "WIRE", "OPTIMIZE"],
        "plain_missing": {
            "AUDIT": "no audit verdict — the symptom was never traced to a prescription or a clean finding",
        },
    },
    "structure": {
        "label": "Check structural quality / is this spaghetti",
        "required": ["STRUCTURE"],
        "conditional": ["REVIEW"],
        "plain_missing": {
            "STRUCTURE": "no structure verdict — the spaghetti check never ran or never concluded",
        },
    },
}

# ---- request-type inference -------------------------------------------------------
# Infer from (a) explicit request lines and (b) which verdict nouns are present.
# Verdict-presence is the stronger signal: a run that produced a SHIP verdict was a
# ship run regardless of how the human phrased it (the suite routes by artifact state,
# not by the verb the user used — chief-engineer Rule 1).
NOUN_TO_TYPE = {
    "SHIP": "ship", "MIGRATE": "ship",
    "CAUSE": "fix", "MAINT": "fix",
    "AUDIT": "audit",
    "OPTIMIZE": "perf", "DATATIER": "perf",
    "SCRUTINY": "scrutinize",
    "REVIEW": "review",
    "SLICE": "build", "GATE": "build", "WIRE": "build",
    "STRUCTURE": "structure",
}
# priority when several types are signalled (a ship run contains build verdicts too —
# classify by the furthest-down-the-lifecycle stage reached).
TYPE_PRIORITY = ["ship", "fix", "audit", "perf", "scrutinize", "review", "build", "structure"]

PHRASE_HINTS = [
    (re.compile(r'\b(ship|release|deploy|roll ?out)\b', re.I), "ship"),
    (re.compile(r'\b(bug|broken|crash|fix|regression|failing)\b', re.I), "fix"),
    (re.compile(r'\b(slow|faster|optimi|perf|latency|throughput)\b', re.I), "perf"),
    (re.compile(r'\b(scrutin|this PR|this diff|this plan|before (it|we) (lands|merge|build))\b', re.I), "scrutinize"),
    (re.compile(r'\b(review|audit|code quality|is this (good|production))\b', re.I), "review"),
    (re.compile(r'\b(spaghetti|maintainab|messy|is this a mess|structur)\b', re.I), "structure"),
    (re.compile(r'\b(build|implement|add (the|a) feature|make it work|create)\b', re.I), "build"),
]


def parse_verdicts(text):
    events = []
    for i, raw in enumerate(text.splitlines(), 1):
        m = NOUN_RE.match(raw)
        if not m:
            continue
        noun = m.group(1)
        if noun not in KNOWN_NOUNS:
            continue
        rest = m.group(2).strip().rstrip('`*')
        state = re.split(r'[(\s|]', rest, maxsplit=1)[0]
        events.append((i, noun, state))
    return events


def infer_type(text, present_nouns):
    # strongest: deepest lifecycle stage actually reached, by verdict presence
    by_priority = [t for t in TYPE_PRIORITY
                   if any(NOUN_TO_TYPE.get(n) == t for n in present_nouns)]
    # ponytail: conditional nouns (MAINT, DATATIER) don't confirm a type without the required co-signal
    if "fix" in by_priority and "CAUSE" not in present_nouns:
        by_priority = [t for t in by_priority if t != "fix"]
    if "perf" in by_priority and "OPTIMIZE" not in present_nouns:
        by_priority = [t for t in by_priority if t != "perf"]
    if by_priority:
        return by_priority[0], "verdict-presence"
    # fallback: phrase hints from the transcript text
    for rx, t in PHRASE_HINTS:
        if rx.search(text):
            return t, "phrase-hint"
    return None, "none"


def analyze(text, forced_type=None):
    events = parse_verdicts(text)
    present = {n for _, n, _ in events}

    if not events:
        return {
            "request_type": None, "inference": "none", "present": [],
            "missing_required": [], "present_conditional": [],
            "verdict": "TRACE: blocked(no verdict lines found — run produced no trace)",
            "exit_code": 2, "events": [],
        }

    if forced_type:
        rtype, how = forced_type, "forced"
    else:
        rtype, how = infer_type(text, present)

    if rtype is None or rtype not in PROFILES:
        # Verdicts exist but we can't map them to a known request profile — report
        # what we saw without inventing a completeness rule (don't fake a profile).
        return {
            "request_type": None, "inference": how,
            "present": sorted(present), "missing_required": [],
            "present_conditional": sorted(present),
            "verdict": f"TRACE: complete(unclassified: {len(present)} verdict(s) present, "
                       f"no completeness profile to check against)",
            "exit_code": 0,
            "events": events, "unclassified": True,
        }

    prof = PROFILES[rtype]
    missing = [n for n in prof["required"] if n not in present]
    present_cond = [n for n in prof["conditional"] if n in present]

    if not missing:
        verdict = (f"TRACE: complete({rtype}: all {len(prof['required'])} "
                   f"required stage(s) present)")
        code = 0
    else:
        verdict = (f"TRACE: incomplete({rtype}: missing {', '.join(missing)}) "
                   f"| review-needed")
        code = 1

    return {
        "request_type": rtype, "inference": how, "label": prof["label"],
        "present": sorted(present), "missing_required": missing,
        "present_conditional": present_cond,
        "all_required": prof["required"], "all_conditional": prof["conditional"],
        "plain_missing": prof.get("plain_missing", {}),
        "verdict": verdict, "exit_code": code, "events": events,
    }


def _format_stage_result(r):
    out = []
    out.append("  Required stages for this kind of work:")
    for n in r["all_required"]:
        mark = "✅" if n in r["present"] else "❌"
        out.append(f"      {mark}  {n}")
    if r["present_conditional"]:
        out.append("")
        out.append("  Optional stages that also ran:")
        for n in r["present_conditional"]:
            out.append(f"      ✅  {n}")
    out.append("")
    if not r["missing_required"]:
        out.append("  ✅  COMPLETE — every stage this kind of work requires reported a")
        out.append("      verdict. The run followed the lifecycle end to end.")
        out.append("")
        out.append("      Caveat (read this): a present verdict proves the stage was")
        out.append("      REPORTED, not that the work behind it was real. This tool")
        out.append("      confirms the run is complete; whether each GATE was DESERVED is")
        out.append("      correctness-gate's and senior-review's call, not this one's.")
    else:
        out.append(f"  ⚠️  INCOMPLETE — {len(r['missing_required'])} required stage(s) "
                   f"never reported:")
        out.append("")
        for n in r["missing_required"]:
            why = r["plain_missing"].get(n, f"the {n} stage was expected but is absent")
            out.append(f"      ❌  {n} — {why}")
        out.append("")
        out.append("      A missing required verdict is (proven) evidence that a stage was")
        out.append("      skipped or never reported. This is the 'I don't know if it built'")
        out.append("      feeling made concrete. Ask the agent to run the missing stage,")
        out.append("      or to show the verdict if it believes the stage did run.")
    return out


def human_report(r):
    out = []
    out.append("=" * 70)
    out.append("RUN TRACE  —  did it actually build?")
    out.append("=" * 70)

    if r["exit_code"] == 2:
        out.append("")
        out.append("  ⛔  NO TRACE — this run produced no verdict lines at all.")
        out.append("      Either no suite skill ran, or the run didn't report verdicts.")
        out.append("      You cannot tell what happened from this transcript. Treat any")
        out.append("      'done' claim in it as unverified — there is no trace to confirm it.")
        out.append("")
        out.append("-" * 70)
        out.append(r["verdict"])
        return "\n".join(out)

    if r.get("unclassified"):
        out.append("")
        out.append(f"  Verdicts present: {', '.join(r['present'])}")
        out.append("  Could not match these to a known request type, so no completeness")
        out.append("  check was applied. The lines exist and are accounted for.")
        out.append("")
        out.append("-" * 70)
        out.append(r["verdict"])
        return "\n".join(out)

    out.append(f"  Request type (inferred by {r['inference']}): {r['label']}")
    out.append("")
    out.extend(_format_stage_result(r))
    out.append("")
    out.append("-" * 70)
    out.append(r["verdict"])
    return "\n".join(out)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Run-completeness trace (did it actually build?).")
    ap.add_argument("path", nargs="?", help="transcript file; stdin if omitted")
    ap.add_argument("--expect", choices=sorted(PROFILES), help="force request type, skip inference")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    text = open(args.path, encoding="utf-8").read() if args.path else sys.stdin.read()
    r = analyze(text, forced_type=args.expect)

    if args.json:
        r_out = {k: v for k, v in r.items() if k != "events"}
        r_out["verdict_events"] = [{"line": l, "noun": n, "state": s} for l, n, s in r["events"]]
        print(json.dumps(r_out, indent=2))
    else:
        print(human_report(r))
    return r["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
