#!/usr/bin/env python3
"""
run.py — puts a real agent through every eval case, with the skills and
without, and writes down the score.

grade.py can tell a right report from a wrong one. Until this file existed,
nothing ever handed a case to an agent, so nobody knew how often an agent
using these skills actually gets it right — or whether it does any better
than the same agent without them. This answers both, with a count.

For each case, each ARM, each REPEAT:

  1. copy the case's fixture/ into a fresh temp folder (the answer key stays
     behind — the agent never sees expect.json or reference/)
  2. run Claude Code headless on the case's words
        with     Claude Code + this plugin, given prompt.md
        without  Claude Code alone, given prompt-plain.md (the same task in
                 plain words, with no skill named — naming a skill the agent
                 does not have would only confuse it)
  3. grade what it WROTE with grade.py, and what it DID from the transcript:
     commands it ran, files it changed, the state it left behind
  4. keep the report, a one-line-per-step action log, and the grades

Then it writes evals/RESULTS.md: one table, with vs without, per case.

Usage
-----
    python evals/run.py                         # every case, both arms, 3 tries each
    python evals/run.py --cases debug-protocol-distant-cause --repeats 1
    python evals/run.py --arms with --model sonnet
    python evals/run.py --dry-run               # show what would run, spend nothing
    python evals/run.py --rescore evals/results/<stamp>   # re-grade saved runs, no agent

Every run costs real usage. --dry-run first if unsure.
"""
import argparse, concurrent.futures, datetime, json, os, re, shutil, subprocess, sys, threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import agent  # noqa: E402
import grade  # noqa: E402
import judge  # noqa: E402

RESULTS_DIR = os.path.join(HERE, "results")
SCORECARD = os.path.join(HERE, "RESULTS.md")
ARMS = ("without", "with")

_print_lock = threading.Lock()


def say(msg):
    with _print_lock:
        print(msg, flush=True)


# ---------------------------------------------------------------- prompts

def prompt_for(case_dir, arm):
    """`with` gets prompt.md; `without` gets prompt-plain.md (falls back to prompt.md)."""
    name = "prompt.md" if arm == "with" else "prompt-plain.md"
    path = os.path.join(case_dir, name)
    if not os.path.isfile(path):
        path = os.path.join(case_dir, "prompt.md")
    return grade.read(path).strip()


# ---------------------------------------------------------------- action checks

def check_actions(spec, parsed, changes, end_output=None, arm="with"):
    """What the agent DID, checked against expect.json's "actions" block.

    Each entry is {"check": plain words, "ok": bool, "detail": why}. Supported:

      read_only        the task is a report: existing files stay unchanged and
                       nothing but notes (.md) is added
      must_run_any     regexes; at least one shell command matches one — e.g.
                       the repro was actually run, not just read
      must_run_before_edit
                       with must_run_any: the match must come before the first
                       change to code — reproduce first, then fix
      must_not_run_any regexes; no shell command matches any — e.g. the deploy
                       script an unattended run must park, not fire
      skills_in_order  (with-skills side only) the agent opened these skills, in
                       this order — a playbook followed, not done from memory
      end_state        after the run, `cmd` is run in the work folder; its output
                       must contain one of `must_print_any` and none of
                       `must_not_print_any` — the fix is real on disk, not in prose
    """
    checks = []
    if not spec:
        return checks

    if spec.get("read_only"):
        code_added = [p for p in changes["added"] if not p.lower().endswith(".md")]
        broken = changes["changed"] + changes["deleted"] + code_added
        checks.append({
            "check": "left the code untouched (a report-only task)",
            "ok": not broken,
            "detail": "changed: " + ", ".join(broken) if broken else "no code file changed",
        })

    commands = parsed["commands"]
    wanted = spec.get("must_run_any")
    if wanted:
        steps = run_steps(parsed["tools"], wanted)
        first_edit = next((i for i, s in enumerate(steps) if s["edits"]), None)
        runs = [i for i, s in enumerate(steps) if s["runs"]]
        # In a command that edits AND runs, order inside it decides: `cat > x.py <<EOF ... EOF;
        # python x.py` ran the new code, not the old; `python -m unittest; sed -i ...` ran first.
        if spec.get("must_run_before_edit") and first_edit is not None:
            good = [i for i in runs if i < first_edit or (i == first_edit and steps[i]["runs_first"])]
            detail = ("ran it before changing any code" if good else
                      "changed the code first; ran it only afterwards" if runs else
                      "never ran it — read or asserted only")
        else:
            good = runs
            detail = "ran it" if good else "never ran it — read or asserted only"
        if good:
            detail += ": " + " ".join(steps[good[0]]["command"].split())[:110]
        checks.append({
            "check": spec.get("must_run_why") or f"actually ran one of: {', '.join(wanted)}",
            "ok": bool(good),
            "detail": detail,
        })

    banned = spec.get("must_not_run_any")
    if banned:
        hit = [c for c in commands if any(re.search(b, executed_part(c)) for b in banned)]
        checks.append({
            "check": spec.get("must_not_run_why") or f"never ran: {', '.join(banned)}",
            "ok": not hit,
            "detail": f"ran: {hit[0][:120]}" if hit else "did not run it",
        })

    order = spec.get("skills_in_order")
    if order and arm == "with":
        opened = [s.split(":")[-1] for s in parsed["skills"]]
        pos, got = 0, []
        for name in opened:
            if pos < len(order) and name == order[pos]:
                got.append(name)
                pos += 1
        checks.append({
            "check": spec.get("skills_why") or "opened " + " → ".join(order) + ", in order",
            "ok": pos == len(order),
            "detail": "opened: " + (" → ".join(opened) or "no skill"),
            # Only the side with skills can be asked this, so it is scored on its own and
            # kept out of the with-vs-without comparison.
            "with_only": True,
        })

    end = spec.get("end_state")
    if end:
        output = grade.normalize(end_output or "")
        ok = (any(grade.normalize(s) in output for s in end.get("must_print_any", [""]))
              and not any(grade.normalize(s) in output for s in end.get("must_not_print_any", [])))
        checks.append({
            "check": end.get("why") or f"after the run, `{end['cmd']}` shows the fix",
            "ok": ok,
            "detail": "printed: " + " ".join((end_output or "").split())[-200:],
        })
    return checks


# Shell commands that write a source file. Heuristic, and deliberately about code:
# writing notes (.md) or scratch output is not changing the thing under test.
SHELL_EDIT = re.compile(
    r"(?:>>?\s*['\"]?[\w./-]+\.(?:py|js|ts|csv|cfg|toml|ini)\b"
    r"|\bsed\s+-i\b|\btee\s+(?:-a\s+)?[\w./-]+\.py\b|\bgit\s+(?:apply|checkout\s+--|restore)\b"
    r"|\bpatch\s+-p)"
)
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\s*(?=\n|$)", re.S)
QUOTED = re.compile(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"")


def executed_part(cmd):
    """A command with the text it only writes or quotes taken out.

    An agent that parks a deploy writes "Off limits: ./deploy.sh" into its notes
    through a heredoc or a commit message. That is the opposite of running it,
    and must not match a check for running it.
    """
    return QUOTED.sub("''", HEREDOC.sub("", cmd))


def run_steps(tools, patterns):
    """Each tool call as {edits, runs, runs_first, command}.

    `runs_first`: within one shell command, the wanted run comes before any edit
    in it — `python -m unittest; cp shipping.py $T; sed -i ... $T/shipping.py`
    ran the real suite first. Text inside heredocs and quotes is ignored for both.
    """
    steps = []
    for t in tools:
        inp = t["input"]
        if t["name"] in EDIT_TOOLS:
            path = str(inp.get("file_path") or inp.get("notebook_path") or "")
            steps.append({"edits": not path.lower().endswith(".md"), "runs": False,
                          "runs_first": False, "command": ""})
        elif t["name"] == "Bash":
            cmd = inp.get("command", "")
            live = executed_part(cmd)
            edit = SHELL_EDIT.search(live)
            hits = [m.start() for m in (re.search(p, live) for p in patterns) if m]
            first_run = min(hits) if hits else None
            steps.append({"edits": bool(edit), "runs": first_run is not None,
                          "runs_first": first_run is not None and (edit is None or first_run < edit.start()),
                          "command": cmd})
        else:
            steps.append({"edits": False, "runs": False, "runs_first": False, "command": ""})
    return steps


def run_end_state(spec, workdir):
    end = (spec or {}).get("end_state")
    if not end:
        return None
    cwd = os.path.join(workdir, end.get("cwd", "fixture"))
    try:
        proc = subprocess.run(end["cmd"], shell=True, cwd=cwd, capture_output=True, text=True,
                              timeout=end.get("timeout", 120), env=agent.clean_env())
        return proc.stdout + proc.stderr
    except (subprocess.TimeoutExpired, OSError) as exc:
        return f"(end-state command failed: {exc})"


def report_text(parsed, workdir, changes):
    """What the agent wrote: its final message, plus any notes files it created."""
    parts = [parsed["final_text"]]
    for rel in changes["added"]:
        if rel.lower().endswith(".md"):
            try:
                parts.append(f"\n\n<!-- file written by the agent: {rel} -->\n"
                             + grade.read(os.path.join(workdir, rel)))
            except (OSError, UnicodeDecodeError):
                pass
    return "".join(parts)


# ---------------------------------------------------------------- one run

def score_run(case, arm, parsed, report, checks, changes, verdict=None):
    """Grade one run from what it wrote and what it did. Pure: used by --rescore too.

    The report is graded on meaning by judge.py when a verdict is given (quotes
    checked against the report), and by grade.py's phrase match otherwise. The
    phrase verdict is kept either way, so the two can be compared.
    """
    graded = grade.grade(case, report)
    by_meaning = bool(verdict and verdict.get("ok"))
    main = verdict if by_meaning else graded
    leaked = agent.touched_answer_key(parsed)
    used_skill = any(agent.skill_matches(s, case["skill"]) for s in parsed["skills"])
    shared = [c for c in checks if not c.get("with_only")]
    own = [c for c in checks if c.get("with_only")]
    ok_actions = all(c["ok"] for c in shared)
    return {
        "case": case["case"], "skill": case["skill"], "arm": arm,
        "passed": main["passed"] and ok_actions and not leaked and not parsed["is_error"],
        "report_passed": main["passed"],
        "graded_by": "meaning" if by_meaning else "phrases",
        "phrase_passed": graded["passed"],
        "judge_text": judge.render(verdict) if verdict else "",
        "actions_passed": ok_actions,
        "followed_skill": all(c["ok"] for c in own) if own else None,
        "leaked": leaked,
        "errored": parsed["is_error"],
        "used_skill": used_skill,
        "skills_loaded": parsed["skills"],
        "found": main["found"], "total": main["total"],
        "missed": [p["what"] for p in main["planted"] if not p["found"]],
        "tripped": [t["what"] for t in main["traps"] if t["tripped"]],
        "action_checks": checks,
        "changes": changes,
        "model": parsed["model"], "models_used": parsed["models_used"],
        "cost_usd": parsed["cost_usd"], "turns": parsed["turns"],
        "grade_text": grade.render(graded),
    }


def one_run(case, arm, i, out_dir, plugin_dir, args):
    tag = f"{case['case']} [{arm} #{i}]"
    workdir = agent.scratch_dir("tte-eval-")
    run_dir = os.path.join(out_dir, case["case"], f"{arm}-{i}")
    os.makedirs(run_dir, exist_ok=True)
    try:
        shutil.copytree(os.path.join(case["dir"], "fixture"), os.path.join(workdir, "fixture"),
                        ignore=shutil.ignore_patterns(*agent.IGNORED_DIRS))
        before = agent.snapshot(workdir)
        prompt = prompt_for(case["dir"], arm)
        say(f"start  {tag}")
        raw = agent.run_agent(prompt, workdir, plugin_dir if arm == "with" else None,
                              model=args.model, timeout=args.timeout, budget_usd=args.budget_usd)
        parsed = agent.parse_stream(raw["lines"])
        if raw["timed_out"]:
            parsed["is_error"] = True
        changes = agent.diff_snapshots(before, agent.snapshot(workdir))
        report = report_text(parsed, workdir, changes)
        end_output = run_end_state(case.get("actions"), workdir)
        checks = check_actions(case.get("actions"), parsed, changes, end_output, arm)
        verdict = None if args.no_judge else judge.judge(case, report)
        if verdict:
            with open(os.path.join(run_dir, "judge.json"), "w", encoding="utf-8") as fh:
                json.dump(verdict, fh, indent=2)

        with open(os.path.join(run_dir, "transcript.jsonl"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(raw["lines"]))
        with open(os.path.join(run_dir, "report.md"), "w", encoding="utf-8") as fh:
            fh.write(agent.redact(report))
        with open(os.path.join(run_dir, "actions.txt"), "w", encoding="utf-8") as fh:
            fh.write(agent.redact(agent.action_log(parsed)) + "\n")
        with open(os.path.join(run_dir, "prompt.md"), "w", encoding="utf-8") as fh:
            fh.write(prompt + "\n")

        result = score_run(case, arm, parsed, report, checks, changes, verdict)
        result.update({"seconds": raw["seconds"], "timed_out": raw["timed_out"],
                       "stderr_tail": raw["stderr"][-600:], "end_output": end_output})
        write_run_grade(run_dir, result)
        say(f"{'PASS ' if result['passed'] else 'fail '}  {tag}  "
            f"{result['found']}/{result['total']} found, ${result['cost_usd'] or 0:.2f}, "
            f"{raw['seconds']:.0f}s")
        if result["errored"] and raw["stderr"].strip():
            say(f"       {tag} agent error: {raw['stderr'].strip().splitlines()[-1][:200]}")
        return result
    finally:
        if not args.keep_workdirs:
            shutil.rmtree(workdir, ignore_errors=True)


def write_run_grade(run_dir, result):
    with open(os.path.join(run_dir, "result.json"), "w", encoding="utf-8") as fh:
        fh.write(agent.redact(json.dumps({k: v for k, v in result.items() if k != "grade_text"}, indent=2)))
    lines = []
    if result.get("judge_text"):
        lines += ["Graded on meaning (judge.py) — this is the verdict that counts:", result["judge_text"], "",
                  "Phrase grader (grade.py), for comparison:"]
    lines += [result["grade_text"], ""]
    for c in result["action_checks"]:
        lines.append(f"  {'ok     ' if c['ok'] else 'FAILED '} {c['check']} — {c['detail']}")
    if result["leaked"]:
        lines.append("  FAILED  the agent reached for the answer key — this run does not count")
    if result["errored"]:
        lines.append("  FAILED  the agent run errored or timed out")
    with open(os.path.join(run_dir, "grade.txt"), "w", encoding="utf-8") as fh:
        fh.write(agent.redact("\n".join(lines)) + "\n")


# ---------------------------------------------------------------- scorecard

def verdict(with_rate, without_rate, n_with, n_without):
    if n_with == 0 or n_without == 0:
        return "only one side was run"
    gap = with_rate - without_rate
    if gap >= 0.5:
        return "**skill helps**"
    if gap >= 0.2:
        return "skill seems to help — run more to be sure"
    if gap <= -0.2:
        return "**skill hurts**"
    if with_rate >= 0.99 and without_rate >= 0.99:
        return "no difference — the agent already does this"
    if with_rate == 0 and without_rate == 0:
        return "both fail — fix the skill or the case"
    return "no clear difference"


def summarize(results):
    by_case = {}
    for r in results:
        by_case.setdefault(r["case"], {"skill": r["skill"], "with": [], "without": []})
        by_case[r["case"]][r["arm"]].append(r)
    return by_case


def rate(runs):
    return sum(1 for r in runs if r["passed"]) / len(runs) if runs else 0.0


def cell(runs):
    if not runs:
        return "—"
    return f"{sum(1 for r in runs if r['passed'])} of {len(runs)}"


def write_scorecard(results, meta, path=SCORECARD):
    by_case = summarize(results)
    cases = {n: grade.load_case(n) for n in by_case}
    total_cost = sum(r["cost_usd"] or 0 for r in results)
    L = []
    L.append("# Scorecard — do the skills make an agent better?\n")
    L.append("Each row is one rigged codebase from `evals/cases/`: a real defect planted in it, and a")
    L.append("trap beside it that a careless agent falls for. A real agent was given the task several")
    L.append("times **without** this plugin (plain Claude Code, the task in plain words) and **with** it.")
    L.append("A try counts as passed only if the agent found everything planted, fell for no trap,")
    L.append("and actually did the work its report claims (checked from its own transcript).\n")
    L.append("Reports are graded on **meaning** by a separate model that is never told which side wrote")
    L.append("them, and must quote the report for every finding it credits; a quote that is not really in")
    L.append("the report does not count. That judge grades every reference report correctly")
    L.append("(`python evals/judge.py --calibrate`).\n")
    L.append(f"- **When:** {meta['started']}")
    L.append(f"- **Model:** {', '.join(meta['models']) or 'unknown'}")
    tries = max((len(row[a]) for row in by_case.values() for a in ARMS), default=0)
    L.append(f"- **Tries per case, per side:** {tries}")
    L.append(f"- **Plugin version:** {meta['version']}")
    L.append(f"- **Cost of this run:** ${total_cost:.2f}")
    L.append(f"- **Raw evidence:** `{meta['out_rel']}/` — every report, action log and grade\n")
    L.append("| Case | Skill | What it tests | Without skills | With skills | Verdict |")
    L.append("|---|---|---|---|---|---|")
    for name, row in sorted(by_case.items()):
        c = cases[name]
        mark = " †" if c.get("baseline_comparable") is False else ""
        L.append(f"| `{name}` | `{row['skill']}` | {c['question']} | {cell(row['without'])}{mark} | "
                 f"{cell(row['with'])} | "
                 f"{verdict(rate(row['with']), rate(row['without']), len(row['with']), len(row['without']))} |")
    if any(cases[n].get("baseline_comparable") is False for n in by_case):
        L.append("\n† This case also grades whether the run went through the skills by name, which an agent")
        L.append("without them cannot do. Read its *Without* column through the outcome checks below, not the total.")

    judged = [r for r in results if r.get("graded_by") == "meaning"]
    if judged:
        agree = sum(1 for r in judged if r["report_passed"] == r["phrase_passed"])
        L.append(f"\n**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on")
        L.append(f"{agree} of {len(judged)} reports. Where they differ, open the run's `grade.txt`: both verdicts are there.")

    with_runs = [r for r in results if r["arm"] == "with"]
    if with_runs:
        used = sum(1 for r in with_runs if r["used_skill"])
        L.append(f"\n**Did the agent open the skill it was asked to use?** {used} of {len(with_runs)} tries.")
        L.append("A try that never opened the skill measured the model, not the skill.")

    followed = {}
    for r in with_runs:
        if r.get("followed_skill") is not None:
            followed.setdefault(r["case"], []).append(r)
    if followed:
        L.append("\n**Did the agent follow the skill's own steps?** Scored apart from the table above, because")
        L.append("only the side with skills can be asked it:")
        for name, runs in sorted(followed.items()):
            n = sum(1 for r in runs if r["followed_skill"])
            detail = next((c for c in runs[0]["action_checks"] if c.get("with_only")), {})
            L.append(f"- `{name}`: {n} of {len(runs)} tries — {detail.get('check', '')}.")
            for r in runs:
                for c in r["action_checks"]:
                    if c.get("with_only") and not c["ok"]:
                        L.append(f"  - one try {c['detail']}")

    L.append("\n## Why tries failed\n")
    failed = [r for r in results if not r["passed"]]
    if not failed:
        L.append("None failed.")
    for r in sorted(failed, key=lambda r: (r["case"], r["arm"])):
        reasons = []
        reasons += [f"missed: {m}" for m in r["missed"]]
        reasons += [f"fell for the trap: {t}" for t in r["tripped"]]
        reasons += [f"did not do it: {c['check']} ({c['detail']})" for c in r["action_checks"]
                    if not c["ok"] and not c.get("with_only")]
        if r["leaked"]:
            reasons.append("looked at the answer key — run discarded")
        if r["errored"]:
            reasons.append("the run errored or timed out")
        L.append(f"- `{r['case']}` **{r['arm']}**: " + ("; ".join(reasons) or "see grade.txt"))

    L.append("\n## How to read this\n")
    L.append("- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.")
    L.append("- **No difference — the agent already does this**: the model gets it right on its own. The")
    L.append("  skill costs attention and adds nothing on this task; make the case harder or cut the skill.")
    L.append("- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.")
    L.append("- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.")
    L.append("\nRe-run with `python evals/run.py` whenever a skill or the model changes.")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(agent.redact("\n".join(L)) + "\n")


def plugin_version():
    with open(os.path.join(agent.ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8") as fh:
        return json.load(fh).get("version", "?")


# ---------------------------------------------------------------- rescore

def rescore(out_dir, use_judge=True, rejudge=False, jobs=6):
    """Re-grade saved runs with the current expect.json. No agent runs; the judge
    runs only for runs that have no saved verdict yet (or all, with rejudge)."""
    todo = []
    for name in sorted(os.listdir(out_dir)):
        case_dir = os.path.join(out_dir, name)
        if not os.path.isdir(case_dir) or name not in grade.case_names():
            continue
        case = grade.load_case(name)
        for run in sorted(os.listdir(case_dir)):
            run_dir = os.path.join(case_dir, run)
            tpath = os.path.join(run_dir, "transcript.jsonl")
            rpath = os.path.join(run_dir, "result.json")
            if not (os.path.isfile(tpath) and os.path.isfile(rpath)):
                continue
            todo.append((case, run_dir, tpath, rpath))

    def one(job):
        case, run_dir, tpath, rpath = job
        with open(rpath, encoding="utf-8") as fh:
            old = json.load(fh)
        parsed = agent.parse_stream(grade.read(tpath).splitlines())
        if old.get("timed_out"):
            parsed["is_error"] = True
        report = grade.read(os.path.join(run_dir, "report.md"))
        checks = check_actions(case.get("actions"), parsed, old["changes"], old.get("end_output"),
                               old["arm"])
        verdict, jpath = None, os.path.join(run_dir, "judge.json")
        if use_judge:
            if os.path.isfile(jpath) and not rejudge:
                with open(jpath, encoding="utf-8") as fh:
                    verdict = json.load(fh)
            else:
                verdict = judge.judge(case, report)
                with open(jpath, "w", encoding="utf-8") as fh:
                    json.dump(verdict, fh, indent=2)
        r = score_run(case, old["arm"], parsed, report, checks, old["changes"], verdict)
        r.update({k: old.get(k) for k in ("seconds", "timed_out", "stderr_tail", "end_output")})
        write_run_grade(run_dir, r)
        return r

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        return list(pool.map(one, todo))


# ---------------------------------------------------------------- main

def main(argv=None):
    grade._utf8_streams()
    ap = argparse.ArgumentParser(description="Run real agents through the eval cases, with and without the skills.")
    ap.add_argument("--cases", nargs="*", help="case names (default: all)")
    ap.add_argument("--arms", default="without,with", help="comma list: with, without")
    ap.add_argument("--repeats", type=int, default=3, help="tries per case per arm (default 3)")
    ap.add_argument("--model", help="model for the agent (default: Claude Code's default)")
    ap.add_argument("--jobs", type=int, default=4, help="runs at once (default 4)")
    ap.add_argument("--timeout", type=int, default=1500, help="seconds per run (default 1500)")
    ap.add_argument("--budget-usd", type=float, default=5.0, help="spend cap per run (default 5)")
    ap.add_argument("--out", help="results folder (default evals/results/<timestamp>); an existing one "
                                  "gets the new tries added beside its old ones")
    ap.add_argument("--no-scorecard", action="store_true", help="don't overwrite evals/RESULTS.md")
    ap.add_argument("--keep-workdirs", action="store_true", help="keep the temp folders for inspection")
    ap.add_argument("--dry-run", action="store_true", help="list the runs and exit")
    ap.add_argument("--rescore", metavar="DIR", help="re-grade a saved results folder; runs no agent")
    ap.add_argument("--no-judge", action="store_true",
                    help="grade reports by phrase match only (free, but misreads some reports)")
    ap.add_argument("--rejudge", action="store_true", help="with --rescore: judge again even if a verdict is saved")
    args = ap.parse_args(argv)

    if args.rescore:
        results = rescore(args.rescore, use_judge=not args.no_judge, rejudge=args.rejudge, jobs=args.jobs)
        meta = json.load(open(os.path.join(args.rescore, "meta.json"), encoding="utf-8"))
        with open(os.path.join(args.rescore, "summary.json"), "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
        if not args.no_scorecard:
            write_scorecard(results, meta)
        print(f"re-graded {len(results)} runs")
        return 0

    names = args.cases or grade.case_names()
    unknown = [n for n in names if n not in grade.case_names()]
    if unknown:
        ap.error(f"unknown case(s): {', '.join(unknown)}")
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    if any(a not in ARMS for a in arms):
        ap.error("--arms takes with and/or without")

    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    out_dir = args.out or os.path.join(RESULTS_DIR, stamp)

    def existing(name, arm):
        """Tries already saved in out_dir, so a second batch adds to them instead of overwriting."""
        d = os.path.join(out_dir, name)
        nums = [int(x.split("-")[-1]) for x in (os.listdir(d) if os.path.isdir(d) else [])
                if x.startswith(arm + "-") and x.split("-")[-1].isdigit()]
        return max(nums, default=0)

    jobs = [(n, a, existing(n, a) + i) for n in names for a in arms for i in range(1, args.repeats + 1)]
    if args.dry_run:
        for n, a, i in jobs:
            print(f"{n:38} {a:8} #{i}")
        print(f"\n{len(jobs)} runs, up to ${len(jobs) * args.budget_usd:.0f} at the per-run cap")
        return 0
    if not shutil.which("claude"):
        print("the `claude` CLI is not on PATH — install Claude Code first", file=sys.stderr)
        return 2

    os.makedirs(out_dir, exist_ok=True)
    plugin_dir = agent.stage_plugin(os.path.join(agent.scratch_dir("tte-plugin-"), "top-tier-engineer"))
    cases = {n: grade.load_case(n) for n in names}

    results = []
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            futures = [pool.submit(one_run, cases[n], a, i, out_dir, plugin_dir, args) for n, a, i in jobs]
            for f in concurrent.futures.as_completed(futures):
                try:
                    results.append(f.result())
                except Exception as exc:  # one broken run must not lose the rest
                    say(f"error  {exc!r}")
    finally:
        shutil.rmtree(os.path.dirname(plugin_dir), ignore_errors=True)

    if os.path.isfile(os.path.join(out_dir, "meta.json")):
        # A batch added to an earlier run: score everything in the folder together.
        results = rescore(out_dir, use_judge=not args.no_judge, jobs=args.jobs)
    meta = {
        "started": stamp, "repeats": args.repeats, "arms": arms, "version": plugin_version(),
        "models": sorted({m for r in results for m in (r["models_used"] or [r["model"]]) if m}),
        "out_rel": os.path.relpath(out_dir, agent.ROOT).replace(os.sep, "/"),
    }
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    if not args.no_scorecard:
        write_scorecard(results, meta)
        print(f"\nscorecard: {os.path.relpath(SCORECARD, agent.ROOT)}")
    passed = sum(1 for r in results if r["passed"])
    print(f"{passed} of {len(results)} runs passed; evidence in {meta['out_rel']}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
