#!/usr/bin/env python3
"""
trigger.py — does verify-loop load when it should, and stay out when it should not?

run.py asks whether the skill makes an agent better once it is loaded. This asks the question
before that one: given a request in a person's own words, does Claude reach for the skill at all?
That is decided by the description in SKILL.md's frontmatter and nothing else, so this is the test
a description change has to pass.

Each prompt in trigger/cases.json runs headless in a fresh copy of trigger/fixture/ (committed)
with trigger/working/ laid over it (the uncommitted change), with only this plugin loaded. A try
"fires" when the agent invokes the skill or reads its SKILL.md within --max-turns. Every try is
also checked for isolation: a user skill, plugin, MCP server or ~/.claude/CLAUDE.md reaching the
child makes the try invalid, because then it measures the person's setup, not the description.

`--description FILE` swaps the description in the staged copy only, so a candidate can be scored
without touching the plugin. Tune on `--split train`; judge the winner on `--split test`.

    python evals/trigger.py --dry-run
    python evals/trigger.py --repeats 2 --jobs 6
    python evals/trigger.py --split train --description cand.txt

Stdlib only. Needs the `claude` CLI on PATH. Every try costs money (about $0.05-0.30).
"""
import argparse, concurrent.futures, datetime, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import agent  # noqa: E402

TRIGGER = os.path.join(HERE, "trigger")
CASES = os.path.join(TRIGGER, "cases.json")
SKILL = "verify-loop"
SKILL_FILE = os.path.join("skills", SKILL, "SKILL.md")
DEFAULT_MODEL = "claude-opus-5-5"


def load_cases(path=CASES):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["cases"]


def pick(cases, split=None, ids=None):
    return [c for c in cases if (not split or c["split"] == split) and (not ids or c["id"] in ids)]


# --- staging -----------------------------------------------------------------------------------

DESCRIPTION = re.compile(r"^description:.*?(?=^\w[\w-]*:)", re.S | re.M)


def set_description(skill_md, text):
    """SKILL.md text with its frontmatter description replaced by `text` (a folded block)."""
    words = " ".join(text.split())
    lines, line = [], ""
    for word in words.split(" "):
        if line and len(line) + 1 + len(word) > 98:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    lines.append(line)
    block = "description: >-\n" + "".join(f"  {l}\n" for l in lines)
    new, count = DESCRIPTION.subn(lambda _: block, skill_md, count=1)
    if count != 1:
        raise ValueError("SKILL.md has no description field to replace")
    return new


def read_description(skill_md):
    m = DESCRIPTION.search(skill_md)
    if not m:
        raise ValueError("SKILL.md has no description field")
    body = m.group(0).split(":", 1)[1].strip()
    if body.startswith((">", "|")):
        body = body.split("\n", 1)[1] if "\n" in body else ""
    return " ".join(body.split())


def stage(dest, description=None):
    agent.stage_plugin(dest)
    if description:
        path = os.path.join(dest, SKILL_FILE)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(set_description(text, description))
    return dest


def make_workdir():
    """fixture/ committed, then working/ laid over it, so `git diff` shows the change."""
    work = agent.scratch_dir("tte-trigger-")
    shutil.copytree(os.path.join(TRIGGER, "fixture"), work, dirs_exist_ok=True)
    git = ["git", "-c", "user.name=eval", "-c", "user.email=eval@example.invalid",
           "-c", "commit.gpgsign=false"]
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "Billing library"]):
        subprocess.run(git + args, cwd=work, check=True, capture_output=True)
    shutil.copytree(os.path.join(TRIGGER, "working"), work, dirs_exist_ok=True)
    return work


# --- reading a try -----------------------------------------------------------------------------

def init_event(lines):
    for line in lines:
        if line.startswith("{") and '"init"' in line:
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("type") == "system" and ev.get("subtype") == "init":
                return ev
    return {}


def user_skill_names():
    """Skill and command names the person has installed for themself."""
    names = set()
    for sub in ("skills", "commands"):
        folder = os.path.join(os.path.expanduser("~"), ".claude", sub)
        if os.path.isdir(folder):
            names |= {os.path.splitext(n)[0] for n in os.listdir(folder)}
    return names


def leaks(init, user_skills, memory_bytes):
    """Why this try saw more than the built-ins plus this plugin; empty means isolated."""
    found = []
    if not init:
        found.append("no init event")
    for p in init.get("plugins") or []:
        if p.get("path") != "builtin" and p.get("name") != SKILL:
            found.append(f"plugin {p.get('name')}")
    for name in init.get("skills") or []:
        if ":" in name and not name.startswith(SKILL + ":"):
            found.append(f"plugin skill {name}")
        elif ":" not in name and name in user_skills:
            found.append(f"user skill {name}")
    if init.get("mcp_servers"):
        found.append("mcp " + ", ".join(m.get("name", "") for m in init["mcp_servers"]))
    if memory_bytes:
        found.append(f"~/.claude/CLAUDE.md ({memory_bytes} chars)")
    return found


def score_try(parsed):
    """Did the skill fire, at which tool call, and which other skills were reached for."""
    fired_at = None
    for i, t in enumerate(parsed["tools"], 1):
        if t["name"] == "Skill" and agent.skill_matches(t["input"].get("skill", ""), SKILL):
            fired_at = i
            break
    if fired_at is None and any(r["skill"] == SKILL for r in parsed["skill_reads"]):
        fired_at = next(i for i, t in enumerate(parsed["tools"], 1)
                        if t["input"].get("file_path", "").replace("\\", "/").endswith(SKILL + "/SKILL.md")
                        or SKILL + "/SKILL.md" in t["input"].get("command", "").replace("\\", "/"))
    others = sorted({s for s in parsed["skills"] if not agent.skill_matches(s, SKILL)})
    return {"fired": fired_at is not None, "fired_at": fired_at, "other_skills": others}


def summarize(tries, cases):
    """Per split: recall on should-fire, false fires on should-not, and per-case counts."""
    by_id = {c["id"]: c for c in cases}
    valid = [t for t in tries if not t["leaks"] and not t["error"]]
    out = {"invalid": len(tries) - len(valid), "splits": {}, "cases": {}}
    for t in valid:
        row = out["cases"].setdefault(t["id"], {"fire": by_id[t["id"]]["fire"],
                                                "split": by_id[t["id"]]["split"],
                                                "fired": 0, "tries": 0, "other_skills": []})
        row["tries"] += 1
        row["fired"] += t["fired"]
        row["other_skills"] = sorted(set(row["other_skills"]) | set(t["other_skills"]))
    for split in ("train", "test", "all"):
        rows = [r for r in out["cases"].values() if split == "all" or r["split"] == split]
        pos = [r for r in rows if r["fire"]]
        neg = [r for r in rows if not r["fire"]]
        hit = sum(r["fired"] for r in pos)
        pos_n = sum(r["tries"] for r in pos)
        false = sum(r["fired"] for r in neg)
        neg_n = sum(r["tries"] for r in neg)
        out["splits"][split] = {
            "fired_when_wanted": f"{hit}/{pos_n}", "fired_when_not": f"{false}/{neg_n}",
            "recall": round(hit / pos_n, 2) if pos_n else None,
            "false_rate": round(false / neg_n, 2) if neg_n else None,
            "right": f"{hit + neg_n - false}/{pos_n + neg_n}",
        }
    return out


def scorecard(summary, meta):
    lines = [f"# Trigger eval: {meta['stamp']}", "",
             f"Model `{meta['model']}`, {meta['repeats']} tries a prompt, --max-turns {meta['max_turns']}. "
             f"Description: {meta['description_source']}.", "",
             f"> {meta['description']}", "",
             "| split | fired when wanted | fired when not | right |", "|---|---|---|---|"]
    for split, s in summary["splits"].items():
        lines.append(f"| {split} | {s['fired_when_wanted']} | {s['fired_when_not']} | {s['right']} |")
    lines += ["", f"Invalid tries (leak or error): {summary['invalid']}. Cost ${meta['cost_usd']:.2f}.", "",
              "| case | split | want | fired | other skills |", "|---|---|---|---|---|"]
    for cid, r in sorted(summary["cases"].items(), key=lambda kv: (not kv[1]["fire"], kv[1]["split"], kv[0])):
        wrong = (r["fired"] < r["tries"]) if r["fire"] else r["fired"] > 0
        lines.append(f"| {cid}{' ✗' if wrong else ''} | {r['split']} | {'fire' if r['fire'] else 'quiet'} | "
                     f"{r['fired']}/{r['tries']} | {', '.join(r['other_skills'])} |")
    return "\n".join(lines) + "\n"


# --- running -----------------------------------------------------------------------------------

def run_try(case, n, plugin_dir, model, max_turns, budget, user_skills, memory_bytes, out_dir):
    work = make_workdir()
    try:
        raw = agent.run_agent(case["prompt"], work, plugin_dir=plugin_dir, model=model,
                              timeout=600, budget_usd=budget, max_turns=max_turns)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    parsed = agent.parse_stream(raw["lines"], plugin_dir)
    row = {"id": case["id"], "try": n, **score_try(parsed),
           "leaks": leaks(init_event(raw["lines"]), user_skills, memory_bytes),
           "error": "timed out" if raw["timed_out"] else ("no result" if not parsed["sessions"] else None),
           "cost_usd": parsed["cost_usd"] or 0.0, "turns": parsed["turns"], "seconds": raw["seconds"]}
    with open(os.path.join(out_dir, f"{case['id']}-{n}.txt"), "w", encoding="utf-8") as fh:
        fh.write(agent.redact(f"{case['prompt']}\n\n{json.dumps(row)}\n\n{agent.action_log(parsed)}\n"))
    return row


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    ap.add_argument("--split", choices=("train", "test"))
    ap.add_argument("--cases", nargs="*", help="case ids")
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max-turns", type=int, default=6)
    ap.add_argument("--budget", type=float, default=0.6, help="USD cap per try")
    ap.add_argument("--description", help="file holding a candidate description for the staged copy")
    ap.add_argument("--out", help="results folder (default evals/results/trigger-<stamp>)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    # A Windows console is cp1252; the scorecard is UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    cases = pick(load_cases(), a.split, a.cases)
    candidate = None
    if a.description:
        with open(a.description, encoding="utf-8") as fh:
            candidate = " ".join(fh.read().split())
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    out_dir = a.out or os.path.join(HERE, "results", f"trigger-{stamp}")
    plugin_dir = stage(os.path.join(tempfile.mkdtemp(prefix="tte-trigger-plugin-"), "plugin"), candidate)
    with open(os.path.join(plugin_dir, SKILL_FILE), encoding="utf-8") as fh:
        description = read_description(fh.read())
    jobs = [(c, n) for c in cases for n in range(1, a.repeats + 1)]
    print(f"{len(cases)} prompts x {a.repeats} = {len(jobs)} tries on {a.model}; description: {description}")
    if a.dry_run:
        return 0

    memory_bytes = agent.user_memory_leak()
    user_skills = user_skill_names()
    os.makedirs(out_dir, exist_ok=True)
    tries = []
    with concurrent.futures.ThreadPoolExecutor(a.jobs) as pool:
        futures = [pool.submit(run_try, c, n, plugin_dir, a.model, a.max_turns, a.budget,
                               user_skills, memory_bytes, out_dir) for c, n in jobs]
        for f in concurrent.futures.as_completed(futures):
            t = f.result()
            tries.append(t)
            flag = "LEAK " + "; ".join(t["leaks"]) if t["leaks"] else (t["error"] or "")
            print(f"  {t['id']} #{t['try']}: {'fired' if t['fired'] else 'quiet'} "
                  f"${t['cost_usd']:.2f} {' '.join(t['other_skills'])} {flag}".rstrip(), flush=True)
    summary = summarize(tries, cases)
    meta = {"stamp": stamp, "model": a.model, "repeats": a.repeats, "max_turns": a.max_turns,
            "description": description, "description_source": a.description or "plugin SKILL.md",
            "cost_usd": sum(t["cost_usd"] for t in tries), "memory_bytes": memory_bytes}
    with open(os.path.join(out_dir, "trigger.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "summary": summary, "tries": sorted(tries, key=lambda t: (t["id"], t["try"]))},
                  fh, indent=2)
    card = scorecard(summary, meta)
    with open(os.path.join(out_dir, "TRIGGER.md"), "w", encoding="utf-8") as fh:
        fh.write(card)
    print(card)
    shutil.rmtree(os.path.dirname(plugin_dir), ignore_errors=True)
    return 1 if summary["invalid"] else 0


if __name__ == "__main__":
    sys.exit(main())
