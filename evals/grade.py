#!/usr/bin/env python3
"""
grade.py — scores a skill's report against a case with a known planted defect.

The skills in this repo are behavioural instructions, so the only honest test is:
give an agent a rigged codebase and the skill, then check whether the report it
wrote names the thing that was actually wrong. This script is the checking half.

Each case under evals/cases/<name>/ holds:

    prompt.md      the words to give the agent (it works on fixture/)
    fixture/       the rigged codebase, defect already planted
    expect.json    what a correct report must contain, and must not claim
    reference/     good.md and bad.md — reports that must pass and must fail,
                   so the grader is itself proven to discriminate

expect.json carries two kinds of expectation, and they are not symmetric:

    planted   things a correct report finds. Each one missed lowers the score.
    traps     things a careless report gets WRONG — a decoy that looks dead but
              is loaded by name, a file that looks clean because nothing parsed
              it. Tripping one fails the case at any score, because a confident
              wrong answer costs the reader more than a miss does.

Usage
-----
    python evals/grade.py --list
    python evals/grade.py <case> --report <path>
    python evals/grade.py --all --reports-dir <dir>      # reads <dir>/<case>.md
    python evals/grade.py <case> --report <path> --json
"""
import argparse, json, os, re, sys

CASES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases")


def _utf8_streams():
    """Keep em-dashes alive on a cp1252 console."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def case_names():
    if not os.path.isdir(CASES_DIR):
        return []
    return sorted(
        d for d in os.listdir(CASES_DIR)
        if os.path.isfile(os.path.join(CASES_DIR, d, "expect.json"))
    )


def load_case(name):
    path = os.path.join(CASES_DIR, name, "expect.json")
    with open(path, encoding="utf-8") as fh:
        case = json.load(fh)
    case["dir"] = os.path.join(CASES_DIR, name)
    return case


def normalize(text):
    """Lowercase, forward-slash the paths, drop backticks, collapse whitespace.

    Reports are prose written by a model, so the same claim arrives spelled a
    dozen ways. Expectations stay robust by listing alternatives; this only
    removes the differences that never carry meaning. Backticks go because a
    report writes `parse.py` mid-sentence and the claim is the same either way.
    Asterisks stay: a verdict in bold is a different claim from the word in a
    table cell, and some traps are written against exactly that.
    """
    flattened = text.replace("\\", "/").replace("`", "").lower()
    return re.sub(r"\s+", " ", flattened)


def says(haystack, needle):
    return normalize(needle) in haystack


# A forbidden phrase is a wrong ANSWER, not a wrong word. The clearest reports
# state the right answer by naming the wrong one and denying it — "do not delete
# csv_out.py", "these are not four copies of one thing" — and a substring match
# cannot tell that apart from a report that recommends the deletion. So a hit is
# discounted only when the denial is attached to it: the cue must sit in the same
# clause and within NEGATION_WINDOW words. That keeps the guard narrow, because a
# trap that stops firing costs more than one that fires too often — "nothing
# imports it, so delete csv_out.py" still trips, the "so" ending the clause that
# held the "nothing".
CLAUSE_BREAK = re.compile(
    r"[.!?;:|]|—|–|\b(?:and|but|so|therefore|thus|however|yet|while|because|since)\b"
)
NEGATION_CUE = re.compile(
    r"\b(?:not|never|no|nor|cannot|avoid|avoids|avoiding|instead|rather|without|"
    r"don't|doesn't|isn't|aren't|won't|can't|wrong|mistake|decoy|beware|resist|"
    r"leave|leaves|leaving|keep|keeps|keeping|stay|stays|untouched|alone)\b"
)
NEGATION_WINDOW = 10  # words between the cue and the phrase it denies


def _is_denied(haystack, start):
    """True when the clause carrying a hit at `start` denies it."""
    head = haystack[:start]
    breaks = list(CLAUSE_BREAK.finditer(head))
    clause = head[breaks[-1].end():] if breaks else head
    return bool(NEGATION_CUE.search(" ".join(clause.split()[-NEGATION_WINDOW:])))


def claim_hits(haystack, needle):
    """(asserted, denied) — how often the phrase is claimed, and merely named."""
    starts = [m.start() for m in re.finditer(re.escape(normalize(needle)), haystack)]
    denied = sum(1 for s in starts if _is_denied(haystack, s))
    return len(starts) - denied, denied


def says_as_claim(haystack, needle):
    """The phrase is asserted somewhere, not only mentioned in order to deny it."""
    return claim_hits(haystack, needle)[0] > 0


def says_any(haystack, needles):
    return any(says(haystack, n) for n in needles)


def says_all(haystack, needles):
    return all(says(haystack, n) for n in needles)


def check_planted(report, item):
    """Found when every required token appears AND one phrasing of the claim does."""
    required = item.get("must_name", [])
    missing = [n for n in required if not says(report, n)]
    claimed = says_any(report, item["must_say_any"])
    return {
        "id": item["id"],
        "what": item["what"],
        "found": not missing and claimed,
        "missing_names": missing,
        "claim_made": claimed,
    }


def check_trap(report, item):
    """Tripped when the report makes the forbidden claim, or fails to hedge.

    `must_not_say_any` is the wrong answer stated outright — asserted, not
    quoted in order to reject it (see `says_as_claim`). `must_say_any` is the
    hedge that has to be there instead — a decoy reported as neither wrong nor
    uncertain is still a trap tripped, because the reader learns nothing and
    believes the sweep was complete.
    """
    said_wrong, denied = [], []
    for phrase in item.get("must_not_say_any", []):
        asserted, refused = claim_hits(report, phrase)
        if asserted:
            said_wrong.append(phrase)
        elif refused:
            denied.append(phrase)
    hedges = item.get("must_say_any", [])
    hedged = says_any(report, hedges) if hedges else True
    return {
        "id": item["id"],
        "what": item["what"],
        "tripped": bool(said_wrong) or not hedged,
        "said": said_wrong,
        "denied": denied,
        "hedged": hedged,
    }


def grade(case, report_text):
    report = normalize(report_text)
    planted = [check_planted(report, i) for i in case.get("planted", [])]
    traps = [check_trap(report, i) for i in case.get("traps", [])]

    found = sum(1 for p in planted if p["found"])
    score = found / len(planted) if planted else 1.0
    tripped = [t for t in traps if t["tripped"]]
    threshold = case.get("pass_score", 1.0)

    return {
        "case": case["case"],
        "skill": case["skill"],
        "score": round(score, 3),
        "pass_score": threshold,
        "found": found,
        "total": len(planted),
        "planted": planted,
        "traps": traps,
        "tripped": len(tripped),
        "passed": score >= threshold and not tripped,
    }


def render(result):
    lines = []
    verdict = "PASS" if result["passed"] else "FAIL"
    lines.append(
        f"{verdict}  {result['case']}  [{result['skill']}]  "
        f"{result['found']}/{result['total']} found, score {result['score']:.2f} "
        f"(needs {result['pass_score']:.2f})"
    )
    for p in result["planted"]:
        lines.append(f"  {'found ' if p['found'] else 'MISSED'}  {p['id']}: {p['what']}")
        if not p["found"]:
            if p["missing_names"]:
                lines.append(f"            never named: {', '.join(p['missing_names'])}")
            if not p["claim_made"]:
                lines.append("            named it, but never said what was wrong with it")
    for t in result["traps"]:
        lines.append(f"  {'TRIPPED' if t['tripped'] else 'held   '} {t['id']}: {t['what']}")
        if t["said"]:
            lines.append(f"            claimed: {'; '.join(t['said'])}")
        elif t["tripped"]:
            lines.append("            never marked it uncertain either")
        if t.get("denied"):
            lines.append(f"            named to reject it, not counted: {'; '.join(t['denied'])}")
    if result["tripped"]:
        lines.append("  a tripped trap fails the case at any score: it is a confident wrong answer")
    return "\n".join(lines)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def main(argv=None):
    _utf8_streams()
    ap = argparse.ArgumentParser(description="Score a skill report against a planted-defect case.")
    ap.add_argument("case", nargs="?", help="case name (see --list)")
    ap.add_argument("--report", help="the agent's report to grade")
    ap.add_argument("--all", action="store_true", help="grade every case")
    ap.add_argument("--reports-dir", help="with --all: directory holding <case>.md")
    ap.add_argument("--list", action="store_true", help="list case names")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    if args.list:
        for name in case_names():
            case = load_case(name)
            print(f"{name:34} {case['skill']:16} {case['question']}")
        return 0

    jobs = []
    if args.all:
        if not args.reports_dir:
            ap.error("--all needs --reports-dir")
        for name in case_names():
            path = os.path.join(args.reports_dir, name + ".md")
            if os.path.isfile(path):
                jobs.append((name, path))
            else:
                print(f"SKIP  {name}: no report at {path}")
    elif args.case and args.report:
        jobs.append((args.case, args.report))
    else:
        ap.error("give a case and --report, or --all with --reports-dir")

    results = [grade(load_case(name), read(path)) for name, path in jobs]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            print(render(r))
            print()

    return 0 if results and all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
