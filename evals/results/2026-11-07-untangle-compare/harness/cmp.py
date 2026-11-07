"""Compare untangle arms on Transcriber_v2 rewound to b3922e1. Adapted copy of the parent's txh.py.

python cmp.py untangle <arm> <id>        arm = ours | caldo
python cmp.py probe <src_repo|x> <D> <id>
python cmp.py regrade <run_dir> <D>      overwrite tests with the real fix's versions, run the cmd
python cmp.py suite <repo> <out.json>
"""
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TX = r"<scratch>\tx"
sys.path.insert(0, r"E:\Me\5.Claude\01 ASSET\Skills\top-tier-engineer\evals")
sys.path.insert(0, os.path.join(TX, "..", "untangle-trace"))
import agent  # noqa: E402
from harness import UNTANGLE_PROMPT  # noqa: E402

BASE = os.path.join(TX, "base")
X = os.path.join(TX, "x")
RUNS = os.path.join(HERE, "runs")
PLUG = os.path.join(HERE, "..", "plugins")
MODEL = "claude-opus-5-5"

ARMS = {"ours": ("untangle", os.path.abspath(os.path.join(PLUG, "ours"))),
        "caldo": ("untangle-codebase", os.path.abspath(os.path.join(PLUG, "caldo")))}

PROBES = {
    "D1": dict(commit="21dbb5a", cmd=["node", "--test", "tests/cutdeck_native_cut.test.cjs"], prompt=(
        "Live rough cut today: close gaps committed all 8,589 moves, then right after that the cut "
        "failed. The read-back said 370 clips were missing (all on audio track 2), but they are all "
        "there in Premiere. Find the root cause and fix it.")),
    "D3": dict(commit="f333ad4", cmd=[sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                      "tests/test_cutdeck_sync_plan.py"], prompt=(
        "I ran Sync on three ~71 minute camera clips of one show and one camera got sent to the back "
        "as unmatched, even though it clearly overlaps the others. The log shows its piece 60-120 s "
        "peaked 1836 s away and the fine match refused it. Find the root cause and fix it.")),
    "D4": dict(commit="a8d613c", cmd=[sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                      "tests/test_cues_grouping.py", "tests/test_cues_policy_config.py"],
               prompt=(
        "Transcribing a clip that is all silence crashes inside faster_whisper.transcribe with "
        "'not enough values to unpack'. Find the root cause and fix it.")),
}


def sh(args, cwd, timeout=900):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def git(repo, *a):
    return sh(["git", *a], repo)


def rmtree(p):
    import stat

    def onexc(fn, path, _):
        os.chmod(path, stat.S_IWRITE)
        fn(path)
    if os.path.exists(p):
        shutil.rmtree(p, onexc=onexc)


def copy_repo(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "node_modules"))


def regrade(repo, d):
    """Copy the repo, overwrite each test file the real fix touched with its version there, run."""
    c = PROBES[d]["commit"]
    g = repo + "-graded2"
    rmtree(g)
    copy_repo(repo, g)
    _, names = git(BASE, "diff", "--name-only", f"{c}^", c, "--", "tests")
    files = [n.strip() for n in names.splitlines() if n.strip()]
    for f in files:
        r = subprocess.run(["git", "show", f"{c}:{f}"], cwd=BASE, capture_output=True)
        dst = os.path.join(g, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(r.stdout)
    rc, out = sh(PROBES[d]["cmd"], g)
    tail = [l for l in out.strip().splitlines() if l.strip()][-4:]
    rmtree(g)
    return {"rc": rc, "files": files, "tail": tail}


def suite(repo):
    rc, out = sh([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", "-rf"],
                 repo, timeout=1800)
    lines = out.splitlines()
    summ = [l for l in lines if re.search(r"\d+ (passed|failed)", l)][-1:]
    failed = sorted(l.split(" ")[1] for l in lines if l.startswith(("FAILED ", "ERROR ")))
    files = [f"tests/{f}" for f in sorted(os.listdir(os.path.join(repo, "tests"))) if f.endswith(".cjs")]
    rc2, out2 = sh(["node", "--test", *files], repo, timeout=1800)
    node = [l.strip() for l in out2.splitlines() if re.match(r"^\s*(#|\u2139) (tests|pass|fail) ", l)]
    node_fail = [l.strip() for l in out2.splitlines() if re.match(r"^\s*not ok ", l)]
    return {"py": summ, "py_failed": failed, "node": node, "node_fail": node_fail[:30],
            "n_py_test_files": len([f for f in os.listdir(os.path.join(repo, "tests")) if f.endswith(".py")]),
            "n_cjs": len(files)}


def run(prompt, workdir, out_dir, plugin_dir=None, budget=8, timeout=3600):
    r = agent.run_agent(prompt, workdir, plugin_dir=plugin_dir, model=MODEL, timeout=timeout,
                        budget_usd=budget)
    open(os.path.join(out_dir, "stream.jsonl"), "w", encoding="utf-8").write("\n".join(r["lines"]))
    open(os.path.join(out_dir, "stderr.txt"), "w", encoding="utf-8").write(r["stderr"] or "")
    p = agent.parse_stream(r["lines"], plugin_dir=plugin_dir)
    keep = {k: p.get(k) for k in ("cost_usd", "num_turns", "usage", "skills_loaded", "skill_reads") if k in p}
    keep["tool_calls"] = len(p.get("tools") or [])
    keep["seconds"], keep["timed_out"] = r["seconds"], r["timed_out"]
    for l in r["lines"]:
        try:
            e = json.loads(l)
        except ValueError:
            continue
        if e.get("type") == "result":
            keep["report"] = e.get("result")
            keep["subtype"] = e.get("subtype")
    try:
        keep["actions"] = agent.action_log(p)
    except Exception as exc:  # noqa: BLE001
        keep["actions"] = str(exc)
    return keep


def dump(out, keep):
    json.dump(keep, open(os.path.join(out, "result.json"), "w", encoding="utf-8"), indent=1, default=str)


def skill_prompt(arm):
    name, pdir = ARMS[arm]
    entry = os.path.join(pdir, "skills", name, "SKILL.md")
    return (UNTANGLE_PROMPT + f"\n\nUse the {name} skill. The explicitly requested {name} skill is at "
            f"{entry}. Read and follow that SKILL.md before starting. You are running unattended: "
            "nobody will answer questions, so make any choice the skill leaves to the user yourself.")


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "untangle":
        arm, rid = sys.argv[2], sys.argv[3]
        out = os.path.join(RUNS, rid)
        os.makedirs(out)
        repo = os.path.join(out, "repo")
        copy_repo(X, repo)
        prompt = skill_prompt(arm)
        open(os.path.join(out, "prompt.txt"), "w", encoding="utf-8").write(prompt)
        keep = run(prompt, repo, out, plugin_dir=ARMS[arm][1], budget=float(os.environ.get("BUDGET", "8")))
        rc, st = git(repo, "status", "--porcelain")
        if st.strip():
            git(repo, "add", "-A")
            sh(["git", "-c", "user.name=dev", "-c", "user.email=dev@example.com", "commit", "-qm",
                "untangle (uncommitted by agent)"], repo)
        keep["diffstat"] = git(repo, "diff", "--shortstat", "b3922e1", "HEAD")[1]
        keep["diff_files"] = git(repo, "diff", "--name-status", "b3922e1", "HEAD")[1]
        keep["suite"] = suite(repo)
        dump(out, keep)
        print(json.dumps({k: keep.get(k) for k in ("cost_usd", "tool_calls", "seconds", "diffstat", "subtype")}, default=str))
        print(json.dumps(keep["suite"]["py"] + keep["suite"]["node"]))
    elif c == "probe":
        src, d, rid = sys.argv[2], sys.argv[3], sys.argv[4]
        out = os.path.join(RUNS, rid)
        os.makedirs(out)
        repo = os.path.join(out, "repo")
        copy_repo(X if src == "x" else src, repo)
        keep = run(PROBES[d]["prompt"], repo, out, budget=4, timeout=1800)
        keep["grade2"] = regrade(repo, d)
        dump(out, keep)
        print(rid, json.dumps({k: keep.get(k) for k in ("cost_usd", "tool_calls", "seconds")}),
              "grade2", keep["grade2"]["rc"], keep["grade2"]["tail"][-1:])
    elif c == "regrade":
        print(json.dumps(regrade(os.path.join(sys.argv[2], "repo"), sys.argv[3])))
    elif c == "suite":
        res = suite(sys.argv[2])
        json.dump(res, open(sys.argv[3], "w", encoding="utf-8"), indent=1)
        print(json.dumps({k: res[k] for k in ("py", "node", "n_cjs")}))
