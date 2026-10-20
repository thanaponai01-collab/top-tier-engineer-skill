#!/usr/bin/env python3
"""
judge.py — grades a report on what it MEANS, not the words it uses.

grade.py matches phrases. That is readable and free, but on real agent reports
it misreads in both directions: "No, it shouldn't go out tonight" is a hold
that never says "hold", and "one caller-less abstraction" contains "one
caller". Worse, a skill teaches the agent its vocabulary, so a phrase grader
quietly rewards the side with the skill for its word choice.

So a second grader reads the report the way a person would: a separate model,
told what the planted findings and the known mistakes are, decides for each
whether the report states it — and must quote the report to prove it. A quote
that is not actually in the report does not count, so the judge cannot invent
support. It is never told which side wrote the report, or which skill exists.

Usage (normally called by run.py)
-----
    python evals/judge.py <case> --report path/to/report.md
    python evals/judge.py --calibrate       # must judge every reference report correctly
"""
import argparse, json, os, re, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import agent  # noqa: E402
import grade  # noqa: E402

JUDGE_MODEL = "sonnet"


def prompt_for(case, report):
    findings = "\n".join(f"- {p['id']}: {p['what']}" for p in case["planted"])
    mistakes = "\n".join(f"- {t['id']}: {t['what']}" for t in case.get("traps", []))
    return f"""You are grading a report an engineer wrote about a small codebase. Grade meaning, not wording:
a finding counts if the report clearly states it in any words. Do not use any tools; answer from the text below.

FINDINGS the report should state:
{findings}

MISTAKES the report must not make (naming a mistake in order to reject it is NOT making it):
{mistakes}

For every finding and every mistake, give a verdict and the shortest exact quote from the report that
shows it — copied character for character, one sentence or less. Use an empty quote when there is none.

Reply with only this JSON:
{{"findings": {{"<id>": {{"stated": true|false, "quote": "..."}}}},
  "mistakes": {{"<id>": {{"made": true|false, "quote": "..."}}}}}}

REPORT:
<<<
{report}
>>>"""


def _plain(text):
    """Emphasis marks aside: a judge quoting **hold** and one quoting hold agree."""
    return grade.normalize(text).replace("*", "").replace("_", " ")


def _quote_ok(quote, report_plain):
    """Every fragment of the quote (split at an ellipsis) is really in the report."""
    parts = [p.strip(" .\"'") for p in re.split(r"\.\.\.|…", _plain(quote or ""))]
    parts = [p for p in parts if p]
    return bool(parts) and sum(map(len, parts)) >= 8 and all(p in report_plain for p in parts)


def parse_verdict(text, case, report):
    """The judge's JSON, with every claim checked against the report itself."""
    match = re.search(r"\{.*\}", text or "", re.S)
    try:
        data = json.loads(match.group(0)) if match else {}
    except ValueError:
        data = {}
    norm = _plain(report)
    planted, traps = [], []
    for p in case["planted"]:
        v = (data.get("findings") or {}).get(p["id"]) or {}
        quoted = _quote_ok(v.get("quote"), norm)
        planted.append({"id": p["id"], "what": p["what"], "found": bool(v.get("stated")) and quoted,
                        "quote": v.get("quote", ""), "quote_checked": quoted})
    for t in case.get("traps", []):
        v = (data.get("mistakes") or {}).get(t["id"]) or {}
        quoted = _quote_ok(v.get("quote"), norm)
        traps.append({"id": t["id"], "what": t["what"], "tripped": bool(v.get("made")) and quoted,
                      "quote": v.get("quote", ""), "quote_checked": quoted})
    found = sum(1 for p in planted if p["found"])
    score = found / len(planted) if planted else 1.0
    return {
        "ok": bool(data),
        "found": found, "total": len(planted), "score": round(score, 3),
        "planted": planted, "traps": traps,
        "passed": bool(data) and score >= case.get("pass_score", 1.0) and not any(t["tripped"] for t in traps),
    }


def judge(case, report, model=JUDGE_MODEL, timeout=300):
    if not report.strip():
        return parse_verdict("{}", case, report)
    workdir = tempfile.mkdtemp(prefix="tte-judge-")
    raw = agent.run_agent(prompt_for(case, report), workdir, None, model=model,
                          timeout=timeout, max_turns=1)
    parsed = agent.parse_stream(raw["lines"])
    verdict = parse_verdict(parsed["final_text"], case, report)
    verdict["cost_usd"] = parsed["cost_usd"]
    verdict["model"] = parsed["model"]
    return verdict


def render(v):
    lines = [f"judge: {'PASS' if v['passed'] else 'FAIL'}  {v['found']}/{v['total']} found"]
    for p in v["planted"]:
        lines.append(f"  {'found ' if p['found'] else 'MISSED'}  {p['id']}"
                     + (f' — "{p["quote"][:120]}"' if p["found"] else ""))
    for t in v["traps"]:
        lines.append(f"  {'TRIPPED' if t['tripped'] else 'held   '} {t['id']}"
                     + (f' — "{t["quote"][:120]}"' if t["tripped"] else ""))
    if not v["ok"]:
        lines.append("  the judge gave no usable verdict")
    return "\n".join(lines)


def calibrate(model=JUDGE_MODEL):
    """The judge on every case's reference reports: good and good-alt must pass, bad must fail.

    The same bar the phrase grader is held to in tests/test_evals.py. A judge
    that can't clear it has no business grading agents.
    """
    import concurrent.futures
    jobs = [(n, r) for n in grade.case_names() for r in ("good", "good-alt", "bad")]

    def one(job):
        name, ref = job
        case = grade.load_case(name)
        v = judge(case, grade.read(os.path.join(case["dir"], "reference", ref + ".md")), model)
        right = v["passed"] == (ref != "bad")
        return name, ref, right, v

    wrong = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for name, ref, right, v in pool.map(one, jobs):
            wrong += not right
            print(f"{'ok   ' if right else 'WRONG'} {name:38} {ref:9} judge says {'PASS' if v['passed'] else 'FAIL'}")
            if not right:
                print("      " + render(v).replace("\n", "\n      "))
    print(f"\n{len(jobs) - wrong} of {len(jobs)} reference reports judged correctly")
    return 1 if wrong else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Grade a report on meaning, with quotes checked.")
    ap.add_argument("case", nargs="?")
    ap.add_argument("--report")
    ap.add_argument("--model", default=JUDGE_MODEL)
    ap.add_argument("--calibrate", action="store_true",
                    help="judge every case's reference reports; exits 1 if any is judged wrongly")
    args = ap.parse_args(argv)
    if args.calibrate:
        return calibrate(args.model)
    if not (args.case and args.report):
        ap.error("give a case and --report, or --calibrate")
    v = judge(grade.load_case(args.case), grade.read(args.report), args.model)
    print(render(v))
    return 0 if v["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
