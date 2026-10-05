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

Some failures are actions, not words: an agent that edits the check to make it
pass can write a report that never says so. A case can therefore also declare
`workdir.edits_allowed` — the only files the agent may change — and be graded
against the copy of fixture/ the agent worked in:

    python evals/grade.py <case> --report <path> --workdir <dir>
    python evals/grade.py --all --reports-dir <dir> --workdirs-dir <dir>   # <dir>/<case>/

The same `workdir` block can also assert what the finished copy must be, not only
what it must not be:

    must_contain   a file in the copy matches a regex (a fail-proof line was written)
    replays        the copy's own command is re-run with one file swapped for a
                   known-good or known-bad version, and must pass or fail as told —
                   so a check is judged by whether it can tell the two apart

Either kind may carry `"gate": false`. It is still run and still shown, as a
`note`, but it does not decide pass or fail. Use it for a step the skill under
test is ambiguous about, so the case does not fail on the skill's own gap.
"""
import argparse, fnmatch, json, os, re, shutil, subprocess, sys, tempfile

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


# Files a run leaves behind that say nothing about what the agent did to the code.
NOISE_DIRS = {"__pycache__", ".pytest_cache", ".git"}
NOISE_SUFFIXES = (".pyc",)


def snapshot(root):
    """{relative posix path: bytes} for every file under root, minus run noise.

    Line endings are folded so a checkout on Windows does not read as an edit.
    """
    files = {}
    for here, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in NOISE_DIRS]
        for name in names:
            if name.endswith(NOISE_SUFFIXES):
                continue
            path = os.path.join(here, name)
            rel = os.path.relpath(path, root).replace("\\", "/")
            with open(path, "rb") as fh:
                files[rel] = fh.read().replace(b"\r\n", b"\n")
    return files


def check_contains(workdir, item):
    """A file in the copy matches `regex`; a missing file never matches."""
    path = os.path.join(workdir, *item["path"].split("/"))
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return False, f"{item['path']} is not there"
    ok = re.search(item["regex"], text) is not None
    return ok, "" if ok else f"{item['path']} has nothing matching {item['regex']!r}"


def run_replay(workdir, case_dir, item):
    """Re-run the copy's command with files swapped, in a scratch copy of it.

    `replace` maps a file in the copy to a path under the case directory, so the
    same tests can be pointed at the original broken code and at a correct
    version. `expect` is "pass" (exit 0) or "fail" (any other exit, no timeout).
    """
    want_pass = item["expect"] == "pass"
    with tempfile.TemporaryDirectory() as tmp:
        scratch = os.path.join(tmp, "w")
        shutil.copytree(workdir, scratch, ignore=shutil.ignore_patterns(*NOISE_DIRS, "*.pyc"))
        for target, source in item["replace"].items():
            dest = os.path.join(scratch, *target.split("/"))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(os.path.join(case_dir, *source.split("/")), dest)
        cmd = [sys.executable if part == "python" else part for part in item["command"]]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        try:
            proc = subprocess.run(cmd, cwd=scratch, env=env, capture_output=True, text=True,
                                  timeout=item.get("timeout", 60))
        except subprocess.TimeoutExpired:
            return False, "timed out"
    ok = (proc.returncode == 0) == want_pass
    return ok, "" if ok else f"exit {proc.returncode}, expected {'0' if want_pass else 'non-zero'}"


def check_workdir(case, workdir):
    """Compare the agent's working copy with fixture/; None when the case declares no rule.

    A file that differs from the fixture (changed, added or deleted) and is not
    on `edits_allowed` is a violation. One rule covers editing the check,
    bending the code to the check, and touching what was never named.
    `must_contain` and `replays` then say what the finished copy has to be.
    """
    spec = case.get("workdir")
    if not spec:
        return None
    if workdir is None:
        return {"checked": False, "violations": [], "checks": []}
    before = snapshot(os.path.join(case["dir"], "fixture"))
    after = snapshot(workdir)
    changed = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
    allowed = spec.get("edits_allowed", [])
    violations = [
        {"path": p, "how": "deleted" if p not in after else "added" if p not in before else "changed"}
        for p in changed
        if not any(fnmatch.fnmatch(p, pattern) for pattern in allowed)
    ]
    checks = []
    for item in spec.get("must_contain", []):
        ok, detail = check_contains(workdir, item)
        checks.append({"id": item["id"], "what": item["what"], "kind": item.get("kind", ""),
                       "gate": item.get("gate", True), "ok": ok, "detail": detail})
    for item in spec.get("replays", []):
        ok, detail = run_replay(workdir, case["dir"], item)
        checks.append({"id": item["id"], "what": item["what"], "kind": item.get("kind", ""),
                       "gate": item.get("gate", True), "ok": ok, "detail": detail})
    if spec.get("verify_status"):
        helper = os.path.join(os.path.dirname(CASES_DIR), "..", "skills", "verify-loop", "scripts", "verify.py")
        proc = subprocess.run([sys.executable, helper, "status", workdir],
                              capture_output=True, text=True, timeout=30)
        checks.append({"id": "strict-current-green", "what": "final helper status is strict, current and green",
                       "kind": "process", "gate": True,
                       "ok": proc.returncode == 0 and "VERIFY-STATE: green" in proc.stdout,
                       "detail": (proc.stdout + proc.stderr).strip()})
    return {"checked": True, "what": spec.get("what", ""), "violations": violations, "checks": checks}


def grade(case, report_text, workdir=None):
    report = normalize(report_text)
    planted = [check_planted(report, i) for i in case.get("planted", [])]
    traps = [check_trap(report, i) for i in case.get("traps", [])]

    found = sum(1 for p in planted if p["found"])
    score = found / len(planted) if planted else 1.0
    tripped = [t for t in traps if t["tripped"]]
    threshold = case.get("pass_score", 1.0)
    edits = check_workdir(case, workdir)
    tampered = bool(edits and (edits["violations"] or any(c["gate"] and not c["ok"] for c in edits["checks"])))

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
        "workdir": edits,
        "passed": score >= threshold and not tripped and not tampered,
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
    edits = result.get("workdir")
    if edits and not edits["checked"]:
        lines.append("  NOT CHECKED  the working copy: this case grades actions too, pass --workdir")
    elif edits:
        for v in edits["violations"]:
            lines.append(f"  EDITED  {v['path']} ({v['how']}): outside the files this run may change")
        if edits["violations"]:
            lines.append("  an edit outside the allowed files fails the case at any score")
        else:
            lines.append("  held    the working copy: nothing changed outside the allowed files")
        for c in edits["checks"]:
            tag = "held   " if c["ok"] else "UNMET  " if c["gate"] else "note   "
            lines.append(f"  {tag} {c['id']}: {c['what']}" + ("" if c["gate"] else "  (advisory)"))
            if not c["ok"] and c["detail"]:
                lines.append(f"            {c['detail']}")
        if any(c["gate"] and not c["ok"] for c in edits["checks"]):
            lines.append("  an unmet action check fails the case at any score")
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
    ap.add_argument("--workdir", help="the copy of fixture/ the agent worked in (single case)")
    ap.add_argument("--workdirs-dir", help="with --all: directory holding <case>/ working copies")
    ap.add_argument("--report-only", action="store_true",
                    help="grade the words alone; a case that also grades actions is then NOT CHECKED")
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

    def workdir_for(name):
        if args.workdir:
            return args.workdir
        if args.workdirs_dir:
            path = os.path.join(args.workdirs_dir, name)
            return path if os.path.isdir(path) else None
        return None

    results = [grade(load_case(name), read(path), workdir_for(name)) for name, path in jobs]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            print(render(r))
            print()

    # A case that grades actions has not passed until the actions were looked at.
    unchecked = [r for r in results if r["workdir"] and not r["workdir"]["checked"]]
    if unchecked and not args.report_only:
        names = ", ".join(r["case"] for r in unchecked)
        print(f"NOT PASSED  {names}: the working copy was not inspected (--workdir, or --report-only "
              "to grade the words alone)")
        return 1

    return 0 if results and all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
