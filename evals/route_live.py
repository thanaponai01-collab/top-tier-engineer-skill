#!/usr/bin/env python3
"""
route_live.py — does the agent pick the right skill on its own?

With 29 skills whose descriptions overlap, choosing one is itself a step an
agent can get wrong, and a skill that never loads does nothing however well it
is written. This puts the plugin in front of a real agent with requests people
actually type (evals/routing.json — none of them names a skill) and records the
FIRST skill the agent opens.

A pick is right when it is in the case's `expect` list. An empty list means no
skill of this plugin should load: a typo fix or a general question is ordinary
work, and a plugin that fires on it is noise.

The agent gets a handful of turns: enough to look at the code before it
chooses, as a careful agent does, but not the whole task. The work after the
choice is not graded here — run.py does that. Each request is written about
the small service in routing.json's `fixture`, so the agent finds what the
request talks about and has a real choice to make.

Usage
-----
    python evals/route_live.py                  # every request once
    python evals/route_live.py --repeats 2
    python evals/route_live.py --dry-run
"""
import argparse, concurrent.futures, datetime, json, os, re, shutil, subprocess, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import agent  # noqa: E402

ROUTING = os.path.join(HERE, "routing.json")
SCORECARD = os.path.join(HERE, "ROUTING.md")
PLUGIN_PREFIX = "top-tier-engineer:"


def load():
    with open(ROUTING, encoding="utf-8") as fh:
        return json.load(fh)


def first_pick(parsed):
    """The first skill opened, or None. Built-in skills count: picking one instead is a miss."""
    return parsed["skills"][0] if parsed["skills"] else None


HINT = re.compile(r"`([a-z][a-z0-9-]+)`")


def hook_hint(prompt, plugin_dir, skills):
    """The skill the plugin's route-hint hook suggests for this prompt, if any.

    The hook's note reaches the agent but is not written to the transcript, so
    it is read here by running the hook itself on the prompt: it is a plain
    script, and gives the same answer every time.
    """
    payload = json.dumps({"prompt": prompt, "session_id": "route-" + uuid.uuid4().hex,
                          "hook_event_name": "UserPromptSubmit", "cwd": plugin_dir})
    env = dict(agent.clean_env(), CLAUDE_PLUGIN_ROOT=plugin_dir)
    try:
        out = subprocess.run([sys.executable, os.path.join(plugin_dir, "tools", "route-hint.py")],
                             input=payload, capture_output=True, text=True, timeout=30, env=env).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    for name in HINT.findall(out):
        if name in skills:
            return name
    return None


def judge(expect, pick):
    """Right when the pick is expected; for `expect: []`, right when none of ours loaded."""
    if not expect:
        return pick is None or not pick.startswith(PLUGIN_PREFIX)
    return pick is not None and any(agent.skill_matches(pick, e) for e in expect)


def one(case, i, fixture, plugin_dir, args):
    workdir = agent.scratch_dir("tte-route-")
    try:
        shutil.copytree(fixture, workdir, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(*agent.IGNORED_DIRS))
        raw = agent.run_agent(case["prompt"], workdir, plugin_dir, model=args.model,
                              timeout=args.timeout, budget_usd=args.budget_usd,
                              max_turns=args.max_turns)
        parsed = agent.parse_stream(raw["lines"])
        pick = first_pick(parsed)
        ok = judge(case["expect"], pick)
        hint = hook_hint(case["prompt"], plugin_dir, set(os.listdir(os.path.join(agent.ROOT, "skills"))))
        hint_ok = judge(case["expect"], PLUGIN_PREFIX + hint if hint else None)
        print(f"{'right' if ok else 'WRONG'}  {pick or '(none)':40} hint={hint or '-':18} ← "
              f"{case['prompt'][:60]}", flush=True)
        return {"prompt": case["prompt"], "expect": case["expect"], "pick": pick, "right": ok,
                "hint": hint, "hint_right": hint_ok, "actions": agent.action_log(parsed, 100),
                "all_skills": parsed["skills"], "try": i, "cost_usd": parsed["cost_usd"],
                "models_used": parsed["models_used"]}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def write_scorecard(results, meta, path=SCORECARD):
    right = sum(1 for r in results if r["right"])
    cost = sum(r["cost_usd"] or 0 for r in results)
    L = ["# Routing — does the agent pick the right skill by itself?\n",
         "Each row is a request someone might really type, naming no skill. The agent had this plugin",
         "loaded and was left to choose. **Right** means the first skill it opened is one that fits;",
         "for the last few rows, the right answer is that no skill of this plugin loads at all.\n",
         f"- **When:** {meta['started']}",
         f"- **Model:** {', '.join(meta['models']) or 'unknown'}",
         f"- **Agent's own pick:** {right} of {len(results)} right",
         f"- **The plugin's hint** (the `route-hint` hook, which fires before the agent thinks): "
         f"{sum(1 for r in results if r['hint_right'])} of {len(results)} right",
         f"- **Cost of this run:** ${cost:.2f}\n",
         "| Request | Should open | Hook hinted | Agent opened | |",
         "|---|---|---|---|---|"]
    for r in results:
        want = ", ".join(f"`{e}`" for e in r["expect"]) or "nothing of this plugin"
        got = f"`{r['pick']}`" if r["pick"] else "nothing"
        hint = f"`{r['hint']}`" if r["hint"] else "—"
        if r["hint"] and not r["hint_right"]:
            hint += " ✗"
        L.append(f"| {r['prompt']} | {want} | {hint} | {got} | {'right' if r['right'] else '**wrong**'} |")
    L.append("\n✗ marks a hint that points at the wrong skill. A hint that is wrong is worse than none: it")
    L.append("pushes the agent toward the wrong instructions.")
    L.append("\nA wrong row is either a description that doesn't say when to use the skill, or two skills")
    L.append("that overlap. Fix the description, or merge the skills, and re-run `python evals/route_live.py`.")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check the agent picks the right skill on its own.")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--model")
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--max-turns", type=int, default=10)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--budget-usd", type=float, default=1.0)
    ap.add_argument("--out", help="results folder (default evals/results/routing-<timestamp>)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    spec = load()
    jobs = [(c, i) for c in spec["cases"] for i in range(1, args.repeats + 1)]
    if args.dry_run:
        for c, i in jobs:
            print(f"#{i} {c['prompt']}")
        print(f"\n{len(jobs)} runs")
        return 0
    if not shutil.which("claude"):
        print("the `claude` CLI is not on PATH — install Claude Code first", file=sys.stderr)
        return 2

    fixture = os.path.join(HERE, spec["fixture"])
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    out_dir = args.out or os.path.join(HERE, "results", f"routing-{stamp}")
    os.makedirs(out_dir, exist_ok=True)
    plugin_dir = agent.stage_plugin(os.path.join(agent.scratch_dir("tte-plugin-"), "top-tier-engineer"))
    results = []
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            futures = [pool.submit(one, c, i, fixture, plugin_dir, args) for c, i in jobs]
            for f in futures:  # keep routing.json's order in the table
                try:
                    results.append(f.result())
                except Exception as exc:
                    print(f"error  {exc!r}", flush=True)
    finally:
        shutil.rmtree(os.path.dirname(plugin_dir), ignore_errors=True)

    meta = {"started": stamp, "models": sorted({m for r in results for m in r["models_used"]})}
    with open(os.path.join(out_dir, "routing.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "results": results}, fh, indent=2)
    write_scorecard(results, meta)
    right = sum(1 for r in results if r["right"])
    print(f"\n{right} of {len(results)} right; table in {os.path.relpath(SCORECARD, agent.ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
