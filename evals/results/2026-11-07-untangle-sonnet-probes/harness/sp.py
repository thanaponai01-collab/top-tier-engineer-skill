"""Sonnet replay probes: does an untangled tree make a weaker agent's next change cheaper and safer?

Each probe is a real later commit of Transcriber_v2 (rewound to b3922e1). A fresh Sonnet agent gets
the bug report or feature ask on an arm's tree. Scored on:
  ok      the commit's own new or changed tests pass (only those, by name: a later commit's file
          also holds tests for earlier fixes the tree never got)
  damage  tests green on the arm's tree before the probe that are red after it
  effort  cost, tokens, tool calls, distinct files read, calls before first touching the fix file
  stray   non-test files the agent changed that the real fix did not touch (reported, not failed)

python sp.py check                 every probe: hidden tests red on the cutoff tree, green with the fix
python sp.py baseline <arm>        cache the arm tree's full-suite red set
python sp.py probe <arm> <P> <n>   one Sonnet run; writes runs/<arm>-<P>-<n>/result.json
python sp.py batch <arms> <Ps> <tries>   comma lists; skips runs already done; BUDGET env caps spend
python sp.py table                 aggregate every result into ../data/probes.json and print the table
"""
import json
import os
import re
import shutil
import stat
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EVALS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, EVALS)
import agent  # noqa: E402

import tempfile  # noqa: E402

TMP = os.environ.get("SP_TMP", os.path.join(tempfile.gettempdir(), "claude"))
OLD = os.path.join(TMP, r"d89b1fd282394482\47860049-54ac-4948-90bd-8f109e33da7e\scratchpad\tx")
CMP = os.path.join(TMP, r"0f604944979403c3\e7339a02-d749-40b3-adc8-8f1c0401c215\scratchpad\cmp\runs")
WORK = os.environ.get("SP_WORK", os.path.join(
    TMP, r"f2ff3cb72949d9ee\350ba390-14df-4f8f-a30b-f508eb7cfd76\scratchpad\sp"))
BASE = os.path.join(OLD, "base")  # full history incl. the 12 later commits
CUT = "b3922e1"
MODEL = os.environ.get("SP_MODEL", "claude-sonnet-5-5")
DATA = os.path.join(HERE, "..", "data")

# arm -> committed tree to copy. New arms (e.g. a fresh 1.41.0 untangle) are added here.
ARMS = {"orig": os.path.join(OLD, "x"),
        "U1": os.path.join(OLD, "runs", "U1", "repo"), "U2": os.path.join(OLD, "runs", "U2", "repo"),
        "O1": os.path.join(CMP, "O1", "repo"), "O2": os.path.join(CMP, "O2", "repo"),
        "C1": os.path.join(CMP, "C1", "repo"), "C2": os.path.join(CMP, "C2", "repo")}
for extra in os.environ.get("SP_ARMS", "").split(";"):
    if "=" in extra:
        k, v = extra.split("=", 1)
        ARMS[k] = v

PY = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
PROBES = {
    "D1": dict(commit="21dbb5a", kind="fix", prompt=(
        "Live rough cut today: close gaps committed all 8,589 moves, then right after that the cut "
        "failed. The read-back said 370 clips were missing (all on audio track 2), but they are all "
        "there in Premiere. Find the root cause and fix it.")),
    "D3": dict(commit="f333ad4", kind="fix", prompt=(
        "I ran Sync on three ~71 minute camera clips of one show and one camera got sent to the back "
        "as unmatched, even though it clearly overlaps the others. The log shows its piece 60-120 s "
        "peaked 1836 s away and the fine match refused it. Find the root cause and fix it.")),
    "D4": dict(commit="a8d613c", kind="fix", prompt=(
        "Transcribing a clip that is all silence crashes with 'ValueError: not enough values to "
        "unpack (expected 2, got 0)', raised in FasterWhisperEngine.transcribe "
        "(transcribe/engines/faster_whisper.py). Find the root cause and fix it.")),
    "P5": dict(commit="a9f1d89", kind="fix", prompt=(
        "Job 62's transcript has multi-second holes mid-sentence: about 12.7 s with no words where "
        "people are clearly talking. The holes are in the tails that the batched tail recovery "
        "re-transcribed, and the words that should be there seem to end up dropped. Find the root "
        "cause and fix it.")),
    "P6": dict(commit="09c52a6", kind="fix", prompt=(
        "Rough cut fails on a sequence that Native Sync laid out, with 'razor filler on audio track 0 "
        "did not land'. Native Sync places audio-only recorder clips between frames, not on the "
        "frame grid. Find the root cause and fix it so the cut is exact.")),
    "P7": dict(commit="60e1b66", kind="feature", prompt=(
        "Sync refuses outright when the active sequence is a _Synced copy. Change it: when the "
        "active sequence is a synced copy, find its original by name (the copy's name minus "
        "\"_Synced\") and sync that instead, reporting the status line "
        "'\"<copy>\" is a synced copy; syncing \"<original>\" instead…' (for example "
        "'\"Shoot_Synced\" is a synced copy; syncing \"Shoot\" instead…'). Still refuse, before "
        "calling the helper, when the original is missing or the name matches more than one "
        "sequence; that refusal keeps today's error text (it still says the sequence is already a "
        "synced copy), with the reason added.")),
}


# ---------- small utils

def sh(args, cwd, timeout=1800):
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def git(repo, *a):
    return sh(["git", *a], repo)


def rmtree(p):
    def onexc(fn, path, _):
        os.chmod(path, stat.S_IWRITE)
        fn(path)
    if os.path.exists(p):
        shutil.rmtree(p, onexc=onexc)


def copy_repo(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "node_modules", ".pytest_cache"))


def show(commit, path):
    r = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=BASE, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def commit_files(c):
    _, out = git(BASE, "diff", "--name-only", f"{c}^", c)
    return [f.strip() for f in out.splitlines() if f.strip()]


def is_test(f):
    return f.startswith("tests/")


def fix_files(c):
    return [f for f in commit_files(c) if not is_test(f) and not f.startswith("docs/")]


# ---------- which tests a commit added or changed, by name

NODE_T = re.compile(r"^\s*test\(\s*([\"'`])((?:(?!\1).)+)\1", re.M)
PY_T = re.compile(r"^def (test_\w+)\(", re.M)


def _blocks(text, rx):
    ms = list(rx.finditer(text))
    out = {}
    for i, m in enumerate(ms):
        name = m.group(2) if rx is NODE_T else m.group(1)
        out[name] = text[m.start(): ms[i + 1].start() if i + 1 < len(ms) else len(text)]
    return out


def changed_tests(c):
    """{test file: [names added or changed in c]}; template names (${...}) are skipped."""
    res = {}
    for f in commit_files(c):
        if not is_test(f) or "/fakes/" in f or not f.endswith((".py", ".cjs")):
            continue
        rx = PY_T if f.endswith(".py") else NODE_T
        new = _blocks((show(c, f) or b"").decode("utf-8", "replace"), rx)
        old = _blocks((show(f"{c}^", f) or b"").decode("utf-8", "replace"), rx)
        names = [n for n, body in new.items() if old.get(n) != body and "${" not in n]
        if names:
            res[f] = names
    return res


def hidden_cmds(c):
    cmds = []
    for f, names in changed_tests(c).items():
        if f.endswith(".py"):
            cmds.append(PY + [f"{f}::{n}" for n in names])
        else:
            pat = "^(" + "|".join(re.escape(n) for n in names) + ")$"
            cmds.append(["node", "--test", f"--test-name-pattern={pat}", f])
    return cmds


def grade(repo, c):
    """Copy repo, drop in c's versions of every test file c touched (fakes included), run only
    c's own new/changed tests. ok = every command exits 0 and ran at least one test."""
    g = repo + "-graded"
    rmtree(g)
    copy_repo(repo, g)
    for f in commit_files(c):
        if is_test(f):
            data = show(c, f)
            if data is not None:
                dst = os.path.join(g, f)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                open(dst, "wb").write(data)
    runs = []
    for cmd in hidden_cmds(c):
        rc, out = sh(cmd, g, timeout=900)
        ran = _count(out)
        runs.append({"cmd": cmd[-1] if cmd[0] == "node" else cmd[len(PY)].split("::")[0],
                     "rc": rc, "ran": ran, "tail": [l for l in out.strip().splitlines() if l.strip()][-3:]})
    rmtree(g)
    return {"ok": bool(runs) and all(r["rc"] == 0 and r["ran"] for r in runs), "runs": runs}


def _count(out):
    m = re.search(r"(\d+) passed", out) or re.search(r"^\S*\s*(?:#|\u2139) tests (\d+)", out, re.M)
    n = int(m.group(1)) if m else 0
    f = re.search(r"(\d+) failed", out) or re.search(r"^\S*\s*(?:#|\u2139) fail (\d+)", out, re.M)
    return n + (int(f.group(1)) if f and "passed" in out else 0)


# ---------- full suite, as a red set

def suite(repo):
    rc, out = sh(PY + ["tests", "-rfE"], repo, timeout=2400)
    py_red = sorted({l.split(" ")[1] for l in out.splitlines() if l.startswith(("FAILED ", "ERROR "))})
    m = re.findall(r"(\d+) passed", out)
    files = sorted(f"tests/{f}" for f in os.listdir(os.path.join(repo, "tests")) if f.endswith(".cjs"))
    rc2, out2 = sh(["node", "--test", "--test-reporter=tap", *files], repo, timeout=2400)
    node_red = sorted({re.sub(r"^\s*not ok \d+ - ", "", l).strip() for l in out2.splitlines()
                       if re.match(r"^\s*not ok \d+ - ", l)})
    node_n = re.findall(r"^# tests (\d+)", out2, re.M)
    return {"py_pass": int(m[-1]) if m else 0, "py_red": py_red,
            "node_tests": int(node_n[-1]) if node_n else 0, "node_red": node_red}


def baseline(arm):
    p = os.path.join(WORK, "baselines", f"{arm}.json")
    if os.path.isfile(p):
        return json.load(open(p, encoding="utf-8"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = os.path.join(WORK, "baselines", f"{arm}-tree")
    rmtree(tmp)
    copy_repo(ARMS[arm], tmp)
    res = suite(tmp)
    rmtree(tmp)
    json.dump(res, open(p, "w", encoding="utf-8"), indent=1)
    return res


# ---------- effort from the stream

FILE_RX = re.compile(r"[\w./\\-]+\.(?:py|js|cjs|mjs|json|md|txt|toml|cfg|ini|html)\b")


def effort(lines, fixes):
    calls, cost, usage = [], 0.0, {}
    for l in lines:
        try:
            e = json.loads(l)
        except ValueError:
            continue
        if e.get("type") == "result":
            if (e.get("total_cost_usd") or 0) >= cost:  # cumulative: keep the last/max
                cost = e.get("total_cost_usd") or 0
                usage = e.get("usage") or {}
        if e.get("type") == "assistant":
            for c in e["message"]["content"]:
                if c.get("type") == "tool_use":
                    calls.append((c["name"], c.get("input") or {}))
    read = set()
    for name, inp in calls:
        if name == "Read":
            read.add(_norm(inp.get("file_path", "")))
        elif name in ("Bash", "PowerShell"):
            cmd = inp.get("command", "")
            if re.search(r"\b(cat|sed|head|tail|less|type|Get-Content|awk|nl)\b", cmd):
                read.update(_norm(x) for x in FILE_RX.findall(cmd))
    base = [os.path.basename(f) for f in fixes]
    first = next((i for i, (n, inp) in enumerate(calls) if any(b in json.dumps(inp) for b in base)), None)
    tokens = sum(usage.get(k) or 0 for k in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                                              "cache_creation_input_tokens"))
    return {"cost": round(cost, 4), "tokens": tokens, "calls": len(calls),
            "files_read": len({r for r in read if r}), "first_fix_touch": first}


def _norm(p):
    p = p.replace("\\", "/")
    for marker in ("/repo/", "repo/"):
        if marker in p:
            p = p.split(marker, 1)[1]
    return p.lstrip("./")


# ---------- one probe

def probe(arm, pid, n):
    pr = PROBES[pid]
    rid = f"{arm}-{pid}-{n}"
    out = os.path.join(WORK, "runs", rid)
    if os.path.isfile(os.path.join(out, "result.json")):
        return json.load(open(os.path.join(out, "result.json"), encoding="utf-8"))
    rmtree(out)
    os.makedirs(out)
    repo = os.path.join(out, "repo")
    copy_repo(ARMS[arm], repo)
    head = git(repo, "rev-parse", "HEAD")[1].strip()
    r = agent.run_agent(pr["prompt"], repo, model=MODEL, timeout=int(os.environ.get("SP_TIMEOUT", "1800")),
                        budget_usd=float(os.environ.get("SP_RUN_BUDGET", "3")))
    open(os.path.join(out, "stream.jsonl"), "w", encoding="utf-8").write("\n".join(r["lines"]))
    open(os.path.join(out, "stderr.txt"), "w", encoding="utf-8").write(r["stderr"] or "")
    fixes = fix_files(pr["commit"])
    git(repo, "add", "-A")
    _, changed = git(repo, "diff", "--cached", "--name-only", head)
    changed = [f for f in changed.split() if f and not f.startswith(".claude/")]
    res = {"run": rid, "arm": arm, "probe": pid, "kind": pr["kind"], "model": MODEL,
           "seconds": r["seconds"], "timed_out": r["timed_out"], **effort(r["lines"], fixes),
           "changed": changed,
           "stray": [f for f in changed if not is_test(f) and not f.startswith("docs/") and f not in fixes],
           "grade": grade(repo, pr["commit"])}
    res["ok"] = res["grade"]["ok"]
    before, after = baseline(arm), suite(repo)
    res["damage"] = sorted(set(after["py_red"]) - set(before["py_red"])) + \
        sorted(set(after["node_red"]) - set(before["node_red"]))
    res["suite_after"] = {k: (len(v) if isinstance(v, list) else v) for k, v in after.items()}
    json.dump(res, open(os.path.join(out, "result.json"), "w", encoding="utf-8"), indent=1)
    if res["ok"]:
        rmtree(repo)  # trees are ~45 MB each; a failed run keeps its tree so it can be regraded
    return res


# ---------- checks and tables

def check():
    """A probe is valid when its hidden tests are red on the cutoff tree and green on cutoff + the
    real fix's code diff. Prints one line per probe; exits 1 if any is invalid."""
    bad = 0
    for pid, pr in PROBES.items():
        c = pr["commit"]
        t = os.path.join(WORK, "check", pid)
        rmtree(t)
        copy_repo(ARMS["orig"], t)
        red = grade(t, c)
        _, diff = git(BASE, "diff", f"{c}^", c, "--", ".", ":!tests", ":!docs")
        p = t + ".diff"
        open(p, "w", encoding="utf-8", newline="\n").write(diff)
        rc, msg = git(t, "apply", p)
        green = grade(t, c) if rc == 0 else {"ok": False, "runs": [msg]}
        valid = (not red["ok"]) and green["ok"]
        bad += not valid
        print(pid, c, "VALID" if valid else "INVALID", "| names:", changed_tests(c),
              "| red-at-cutoff:", [x["rc"] for x in red["runs"]], "green-with-fix:",
              [x["rc"] if isinstance(x, dict) else x for x in green["runs"]])
        rmtree(t)
        os.remove(p)
    sys.exit(1 if bad else 0)


def table():
    rows = []
    for d in sorted(os.listdir(os.path.join(WORK, "runs"))):
        p = os.path.join(WORK, "runs", d, "result.json")
        if os.path.isfile(p):
            j = json.load(open(p, encoding="utf-8"))
            j.pop("grade", None)
            rows.append(j)
    os.makedirs(DATA, exist_ok=True)
    json.dump(rows, open(os.path.join(DATA, "probes.json"), "w", encoding="utf-8"), indent=1)
    group = lambda a: {"orig": "orig", "U": "plain", "O": "ours", "C": "caldo"}.get(a[0] if a != "orig" else a, a)  # noqa: E731
    cells = {}
    for r in rows:
        cells.setdefault((group(r["arm"]), r["probe"]), []).append(r)
    arms = sorted({k[0] for k in cells}, key=["orig", "plain", "ours", "caldo"].index if all(
        k[0] in ("orig", "plain", "ours", "caldo") for k in cells) else str)
    print("| arm | probe | ok | damage runs | mean cost | mean tokens | mean calls | mean files read | mean calls to fix file | stray runs |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for a in arms:
        for pid in PROBES:
            rs = cells.get((a, pid))
            if not rs:
                continue
            m = lambda k: sum(x[k] or 0 for x in rs) / len(rs)  # noqa: E731
            ft = [x["first_fix_touch"] for x in rs if x["first_fix_touch"] is not None]
            print(f"| {a} | {pid} | {sum(x['ok'] for x in rs)}/{len(rs)} | {sum(bool(x['damage']) for x in rs)} "
                  f"| ${m('cost'):.2f} | {m('tokens')/1000:.0f}k | {m('calls'):.0f} | {m('files_read'):.0f} "
                  f"| {sum(ft)/len(ft) if ft else float('nan'):.0f} | {sum(bool(x['stray']) for x in rs)} |")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "check":
        check()
    elif cmd == "baseline":
        print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in baseline(sys.argv[2]).items()}))
    elif cmd == "probe":
        r = probe(sys.argv[2], sys.argv[3], sys.argv[4])
        print(json.dumps({k: r[k] for k in ("run", "ok", "damage", "cost", "tokens", "calls", "files_read",
                                             "first_fix_touch", "stray", "seconds")}))
    elif cmd == "batch":
        arms, pids, tries = sys.argv[2].split(","), sys.argv[3].split(","), int(sys.argv[4])
        cap, spent = float(os.environ.get("BUDGET", "0") or 0), 0.0
        for n in range(1, tries + 1):
            for pid in pids:
                for arm in arms:
                    if cap and spent >= cap:
                        print("BUDGET reached", round(spent, 2))
                        sys.exit(0)
                    r = probe(arm, pid, str(n))
                    spent += r["cost"]
                    print(r["run"], "ok" if r["ok"] else "FAIL", f"${r['cost']:.2f}", r["calls"], "calls",
                          "damage" if r["damage"] else "", flush=True)
        print("spent", round(spent, 2))
    elif cmd == "table":
        table()
