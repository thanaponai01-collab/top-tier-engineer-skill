#!/usr/bin/env python3
"""perf.py - the mechanical side of the perf-optimize skill.

A model that reads the code well usually finds the slow part and fixes it. This keeps what it
skips: the time of the code as it was, at two sizes so growth shows; a profile saying where the
time went; proof that each change kept the output and beat the noise; and a guard the suite runs
that fails when a gain is taken back out.

  P                         the workloads recorded and what is next
  P --measure CMD --size N [--runs K]
                            run CMD (a workload that prints the result) on the code as it was, in a
                            throwaway copy: K timed runs (default 5, fewer once a minute is spent), then
                            one profiled run. Refused when it exits non-zero or prints differently
                            between runs. The first measure keeps the tree as it was in .perf/before/
  P --gate [--guard CMD]    check the stages and print every problem with its fix:
    1 measure  two workloads at different sizes, timed on the code as it was, at least one profiled
    2 change   after a change, every workload prints exactly what it printed, every one is faster
               beyond the noise (the slowest run now under the fastest of the code as it was, runs alternated
               unless the gain is 3x past the recorded range), and every changed
               function held at least 2% of a profile, or has `- FILE::FUNC: <why>` in .perf/notes.md
    3 guard    after a change, the guard passes now and fails with each changed file put back alone

`P` is `python perf.py <repo>`. Stdlib only.
"""
import argparse, ast, glob, hashlib, json, math, os, pstats, re, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _encoding import utf8_streams  # noqa: E402

STATE = ".perf"
BEFORE = f"{STATE}/before"
LEDGER = f"{STATE}/state.json"
NOTES = f"{STATE}/notes.md"
FILL = "[[fill"
NOT_PRODUCT = {".git", "__pycache__", "node_modules", ".venv", "venv", STATE, ".debug", ".wire", ".latent",
               ".features", ".structure", ".threat", ".verify-state-cache", ".pytest_cache", ".mypy_cache",
               ".ruff_cache", ".evolve", ".release", ".blast", ".mistakes", ".formal"}
NOT_PRODUCT_FILES = {".verify-state.json"}
BASH = shutil.which("bash")
NO_TESTS = re.compile(r"^Ran 0 tests\b|\bno tests ran\b", re.MULTILINE | re.IGNORECASE)
MIN_SHARE = 0.02
SPEND = 60.0   # seconds of timed runs per workload before stopping early
SLOW = 20.0    # one run longer than this is timed once and not profiled: a smaller size's profile stands
CLEAR = 3.0    # a gain this many times past the recorded range needs no fresh runs of the old code

PROFILER = r'''import atexit, cProfile, os
if os.environ.get("PERF_PROFILE_DIR"):
    _pf = cProfile.Profile()
    _pf.enable()
    def _pf_dump():
        _pf.disable()
        try:
            _pf.dump_stats(os.path.join(os.environ["PERF_PROFILE_DIR"], f"{os.getpid()}.prof"))
        except Exception:
            pass
    atexit.register(_pf_dump)
'''


def rel(path, root):
    return os.path.relpath(path, root).replace(os.sep, "/")


def walk_files(root):
    for d, subdirs, names in os.walk(root):
        subdirs[:] = sorted(s for s in subdirs if s not in NOT_PRODUCT)
        for n in sorted(names):
            if n not in NOT_PRODUCT_FILES and not n.endswith(".pyc"):
                yield os.path.join(d, n)


def product_files(root):
    """{rel path: sha} for every file that is the product, not a tool's state."""
    out = {}
    for p in walk_files(root):
        with open(p, "rb") as fh:
            out[rel(p, root)] = hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()[:16]
    return out


def is_test(r):
    name = r.rsplit("/", 1)[-1]
    return r.startswith(("tests/", "test/")) or "/tests/" in r or name.startswith("test_") or name.endswith("_test.py")


def read_json(repo, rel_path, default=None):
    try:
        with open(os.path.join(repo, rel_path), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def save(repo, ledger):
    path = os.path.join(repo, LEDGER)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(ledger, fh, indent=1, sort_keys=True)


def changed_files(repo):
    """Product files (not tests) that differ from .perf/before/."""
    before = os.path.join(repo, BEFORE)
    if not os.path.isdir(before):
        return []
    was, now = product_files(before), product_files(repo)
    return sorted(f for f in was if now.get(f) != was[f] and not is_test(f))


def scratch(repo, put_back=()):
    """A throwaway copy of the tree now, with PUT_BACK files restored from .perf/before/."""
    tmp = tempfile.mkdtemp(prefix="perf-")
    root = os.path.join(tmp, "repo")
    shutil.copytree(repo, root, ignore=shutil.ignore_patterns(*NOT_PRODUCT, "*.pyc"))
    for f in put_back:
        src = os.path.join(repo, BEFORE, *f.split("/"))
        dest = os.path.join(root, *f.split("/"))
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(src, dest)
        elif os.path.exists(dest):
            os.remove(dest)
    return tmp, root


def run(root, cmd, timeout, profile_dir=None):
    """(exit or 'timeout', stdout, stderr, seconds) of CMD run in ROOT."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if profile_dir:
        hook = os.path.join(profile_dir, "hook")
        os.makedirs(hook, exist_ok=True)
        with open(os.path.join(hook, "sitecustomize.py"), "w", encoding="utf-8") as fh:
            fh.write(PROFILER)
        env["PERF_PROFILE_DIR"] = profile_dir
        env["PYTHONPATH"] = os.pathsep.join([hook] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    argv = [BASH, "-c", cmd] if BASH else cmd
    start = time.perf_counter()
    try:
        p = subprocess.run(argv, cwd=root, shell=not BASH, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return "timeout", "", "timed out", time.perf_counter() - start
    return p.returncode, (p.stdout or "").replace("\r\n", "\n"), p.stderr or "", time.perf_counter() - start


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def tail(text, n=3):
    return [ln[:160] for ln in text.splitlines() if ln.strip()][-n:]


def timed(root, cmd, runs, timeout):
    """Timed runs of CMD. ({'times', 'out', 'sha'}, problem or None)."""
    times, out = [], None
    for i in range(runs):
        code, stdout, stderr, secs = run(root, cmd, timeout)
        if code != 0:
            return None, f"`{cmd}` exited {code}: {' / '.join(tail(stderr or stdout))}"
        if out is not None and stdout != out:
            return None, (f"`{cmd}` printed something different on run {i + 1}: a workload whose output moves "
                          "cannot show that a change kept it. Fix the seed or the clock, then measure again")
        out = stdout
        times.append(round(secs, 4))
        if sum(times) > SPEND or secs > SLOW:
            break
    return {"times": times, "sha": sha(out), "out": tail(out, 6)}, None


def interleaved(repo, files, cmd, runs, timeout, recorded=None):
    """Alternate runs of CMD on the code as it was and on the tree now, so drift hits both alike.
    (now, as it was, problem or None)."""
    tmp_b, before = scratch(repo, files)
    tmp_n, now = scratch(repo)
    try:
        sides = {"was": {"times": [], "out": None}, "now": {"times": [], "out": None}}
        for i in range(runs):
            for side, root in (("now", now), ("was", before)):
                if side == "was" and sides["now"]["times"] and recorded and                         max(sides["now"]["times"]) * CLEAR < min(recorded["times"]):
                    continue   # far past the noise: the recorded runs of the old code stand
                if side == "was" and sides["was"]["times"] and (sum(sides["was"]["times"]) > SPEND
                                                               or max(sides["was"]["times"]) > SLOW):
                    continue
                code, stdout, stderr, secs = run(root, cmd, timeout)
                if code != 0:
                    where = "the code as it was" if side == "was" else "the tree now"
                    return None, None, f"`{cmd}` exited {code} on {where}: {' / '.join(tail(stderr or stdout))}"
                if sides[side]["out"] is not None and stdout != sides[side]["out"]:
                    return None, None, f"`{cmd}` printed something different on run {i + 1}: fix the seed or the clock"
                sides[side]["out"] = stdout
                sides[side]["times"].append(round(secs, 4))
        out = {k: {"times": v["times"], "sha": sha(v["out"]), "out": tail(v["out"], 6)} for k, v in sides.items()
               if v["times"]}
        return out["now"], out.get("was") or recorded, None
    finally:
        shutil.rmtree(tmp_b, ignore_errors=True)
        shutil.rmtree(tmp_n, ignore_errors=True)


def profiled(root, cmd, timeout):
    """The top functions in the repo and outside it from one profiled run, by share of the time."""
    pdir = tempfile.mkdtemp(prefix="perf-prof-")
    try:
        run(root, cmd, timeout, profile_dir=pdir)
        files = glob.glob(os.path.join(pdir, "*.prof"))
        if not files:
            return None
        stats = pstats.Stats(*files).stats
    except Exception:
        return None
    finally:
        shutil.rmtree(pdir, ignore_errors=True)
    total = sum(v[2] for v in stats.values()) or 1e-9
    base = os.path.normcase(os.path.abspath(root))
    mine, other = [], []
    for (path, line, name), (_, ncalls, tt, ct, _callers) in stats.items():
        p = os.path.normcase(os.path.abspath(path)) if path not in ("~", "") else ""
        row = {"ncalls": ncalls, "own": round(tt / total, 4), "share": round(ct / total, 4)}
        if p.startswith(base + os.sep) and not rel(p, base).startswith(STATE):
            row.update(func=f"{rel(p, base)}::{name}", line=line)
            mine.append(row)
        elif path == "~":
            row.update(func=name)
            other.append(row)
    mine.sort(key=lambda r: -r["share"])
    other.sort(key=lambda r: -r["own"])
    funcs = [r for r in mine if not r["func"].endswith("::<module>")]
    return {"mine": funcs[:20] + [r for r in mine if r["func"].endswith("::<module>")][:3], "other": other[:6]}


def number(label):
    m = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)", str(label))
    return float(m.group(1)) if m else None


def summary(t):
    s = sorted(t["times"])
    return f"median {s[len(s) // 2]:.3f}s, range {s[0]:.3f}-{s[-1]:.3f}s over {len(s)} run{'s' if len(s) != 1 else ''}"


def median(t):
    s = sorted(t["times"])
    return s[len(s) // 2]


def measure(repo, cmd, size, runs, timeout):
    if size is None:
        print("refused: give the workload's size with --size (rows, users, requests), so growth can be read")
        return 2
    ledger = read_json(repo, LEDGER, {})
    before = os.path.join(repo, BEFORE)
    if not os.path.isdir(before):
        shutil.copytree(repo, before, ignore=shutil.ignore_patterns(*NOT_PRODUCT, "*.pyc"))
    put_back = changed_files(repo)
    tmp, root = scratch(repo, put_back)
    try:
        t, problem = timed(root, cmd, runs, timeout)
        if problem:
            print(f"refused: {problem}")
            return 1
        prof = profiled(root, cmd, timeout) if max(t["times"]) <= SLOW else None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    works = [w for w in ledger.get("workloads", []) if not (w["cmd"] == cmd and str(w["size"]) == str(size))]
    works.append({"cmd": cmd, "size": str(size), "before": t, "profile": prof})
    ledger["workloads"] = works
    save(repo, ledger)
    print(f"measured `{cmd}` at size {size} on the code as it was"
          + (f" (with {', '.join(put_back)} put back)" if put_back else "") + f": {summary(t)}")
    if prof:
        print("profile, share of the time spent inside each function (calls):")
        for r in prof["mine"][:8]:
            print(f"  {r['share'] * 100:5.1f}%  {r['func']}  ({r['ncalls']} calls)")
        for r in prof["other"][:3]:
            print(f"  {r['own'] * 100:5.1f}% own  {r['func']}  ({r['ncalls']} calls)")
    elif max(t["times"]) > SLOW:
        print(f"not profiled: one run took over {SLOW:.0f}s, so a smaller size's profile stands for it")
    else:
        print("no profile: the workload ran no Python this helper could profile. Profile it with the stack's own tool")
    print("next: measure a second size, change one thing, then P --gate")
    return 0


def functions(path):
    """{qualname: source with decorators} for every function and class method in a Python file."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        tree = ast.parse(text)
    except (OSError, SyntaxError, ValueError):
        return None
    lines = text.splitlines()
    out = {}

    def visit(body, prefix):
        for n in body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start = (n.decorator_list[0].lineno if n.decorator_list else n.lineno) - 1
                if not isinstance(n, ast.ClassDef):
                    out[prefix + n.name] = "\n".join(lines[start:n.end_lineno])
                visit(n.body, prefix + n.name + ".")
    visit(tree.body, "")
    return out


def changed_functions(repo, files):
    out = []
    for f in files:
        if not f.endswith(".py"):
            out.append(f"{f}::*")
            continue
        was = functions(os.path.join(repo, BEFORE, *f.split("/"))) or {}
        now = functions(os.path.join(repo, *f.split("/"))) or {}
        diff = sorted(q for q in set(was) | set(now) if was.get(q) != now.get(q))
        out += [f"{f}::{q}" for q in diff] or [f"{f}::<module>"]
    return out


def read_notes(repo):
    notes = {}
    try:
        with open(os.path.join(repo, NOTES), encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"\s*-\s*(\S+?::\S+?)\s*:\s*(.*)$", line)
                if m:
                    notes[m.group(1)] = m.group(2).strip()
    except OSError:
        pass
    return notes


def profile_share(works, func):
    """The largest share FUNC held in any workload's profile (a method matches by its last name)."""
    path, _, qual = func.partition("::")
    name = qual.rsplit(".", 1)[-1]
    best = 0.0
    for w in works:
        for r in (w.get("profile") or {}).get("mine", []):
            if r["func"] == f"{path}::{name}" or (qual == "<module>" and r["func"] == f"{path}::<module>"):
                best = max(best, r["share"])
    return best


def guard_run(repo, cmd, timeout, put_back=()):
    tmp, root = scratch(repo, put_back)
    try:
        code, out, err, _ = run(root, cmd, timeout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if NO_TESTS.search(out + err):
        return "no tests", tail(out + err, 1)
    if code == "timeout":
        return "fail", ["timed out"]
    return ("pass" if code == 0 else "fail"), tail(out + err, 1)


def gate(repo, guard, timeout):
    ledger = read_json(repo, LEDGER, {})
    problems = {1: [], 2: [], 3: []}
    print('P = python "' + os.path.abspath(__file__) + '" ' + repo)
    works = ledger.get("workloads", [])
    if not works:
        problems[1].append('nothing measured. Run the workload that shows the slowness on the code as it was: '
                           'P --measure "<cmd>" --size <N>, then again at a bigger size')
    elif len({w["size"] for w in works}) < 2:
        problems[1].append(f"one size measured ({works[0]['size']}). Measure the same work at a second, bigger "
                           "size (generate the input in a scratch folder if you must), so growth shows")
    if works and not any(w.get("profile") for w in works):
        problems[1].append("no workload has a profile, so no change can be traced to one. Measure a size that "
                           f"runs under {SLOW:.0f}s, or profile with the stack's own tool and name the hot "
                           f"functions in {NOTES}")

    files = changed_files(repo)
    funcs = changed_functions(repo, files) if files else []
    notes = read_notes(repo)
    if files and works:
        for w in works:
            t, again, problem = interleaved(repo, files, w["cmd"], max(len(w["before"]["times"]), 3), timeout,
                                          recorded=w["before"])
            w["after"], w["again"] = t, again
            if problem:
                problems[2].append(f"on the tree now, {problem}")
                continue
            if t["sha"] != w["before"]["sha"]:
                problems[2].append(f"`{w['cmd']}` (size {w['size']}) prints something different now. A fast wrong "
                                   f"answer is not a gain: put back the change that moved it. Now ends: {' / '.join(t['out'][-2:])}")
            if max(t["times"]) >= min(again["times"]):
                problems[2].append(f"`{w['cmd']}` (size {w['size']}) is not faster beyond the noise: now "
                                   f"{summary(t)}, the code as it was {summary(again)} (runs alternated). Keep a "
                                   "change only when its slowest run beats the fastest run before; otherwise put it back")
        for fn in funcs:
            share = profile_share(works, fn)
            reason = notes.get(fn, "")
            if share >= MIN_SHARE or (reason and not reason.startswith(FILL) and len(reason.split()) >= 4):
                continue
            problems[2].append(f"{fn} changed, but no profile gave it {MIN_SHARE:.0%} of the time ({share:.1%}). "
                               f"Put it back, or say why the gain needs it in {NOTES}: `- {fn}: <why>`")
        save(repo, ledger)

    guard = guard or (ledger.get("guard") or {}).get("cmd")
    guard_result = {}
    if files:
        if not guard:
            problems[3].append('no guard. Leave a check in the suite that fails when the gain is taken out (a '
                               'count of calls or queries, or a time on a big input with room to spare), then '
                               'P --gate --guard "<test cmd>"')
        else:
            status, out = guard_run(repo, guard, timeout)
            guard_result["now"] = status
            if status != "pass":
                problems[3].append(f"the guard `{guard}` does not pass on the tree now ({status}: {' / '.join(out)})")
            for f in files:
                bstatus, bout = guard_run(repo, guard, timeout, put_back=[f])
                guard_result[f] = bstatus
                if bstatus != "fail":
                    problems[3].append(f"with only {f} put back as it was, the guard {'still passes' if bstatus == 'pass' else 'runs no tests'}. "
                                       f"Guard the gain {f} brings, or put it back if it brings none")
        ledger["guard"] = {"cmd": guard, **guard_result} if guard else {}
        save(repo, ledger)

    names = {1: "measure: the code as it was, timed and profiled at two sizes",
             2: "change: " + ("same output, faster beyond the noise, every change aimed by a profile" if files
                              else "no product file changed (diagnosis only)"),
             3: "guard: " + ("a kept check fails with each change put back" if files else "nothing to guard")}
    for g in (1, 2, 3):
        print(f"STAGE {g} {names[g]}: " + ("holds" if not problems[g] else f"open, {len(problems[g])} to fix"))
        for line in problems[g]:
            print(f"  - {line}")
    open_stages = [g for g in (1, 2, 3) if problems[g]]
    if open_stages:
        print(f"PERF-GATE: open({', '.join(map(str, open_stages))}): fix the lines above, then P --gate")
        return 1
    answer(works, files, funcs, guard)
    return 0


def growth(works):
    """Lines saying how time and calls grow between the smallest and largest size of the same command."""
    lines = []
    sized = sorted((w for w in works if number(w["size"]) is not None), key=lambda w: number(w["size"]))
    if len(sized) < 2:
        return lines
    small, big = sized[0], sized[-1]
    sr = number(big["size"]) / max(number(small["size"]), 1e-9)
    tr = median(big["before"]) / max(median(small["before"]), 1e-9)
    k = math.log(tr) / math.log(sr) if sr > 1 and tr > 0 else 0
    lines.append(f"From size {small['size']} to {big['size']} ({sr:g}x), the time grew {tr:.1f}x"
                 + (f": faster than the input (about n^{k:.1f})" if k > 1.3 else ": about in step with the input"
                    if k > 0.6 else ": less than the input (fixed costs dominate)") + ".")
    calls = {r["func"]: r["ncalls"] for r in (small.get("profile") or {}).get("mine", []) + (small.get("profile") or {}).get("other", [])}
    for r in ((big.get("profile") or {}).get("mine", []) + (big.get("profile") or {}).get("other", []))[:12]:
        c = calls.get(r["func"])
        if c and r["ncalls"] / c > sr * 1.5:
            lines.append(f"  {r['func']}: {c} calls -> {r['ncalls']}, faster than the input")
    return lines


def answer(works, files, funcs, guard):
    print("\nANSWER (drafted from the recorded runs; give it, adding only context):\n")
    for w in sorted(works, key=lambda w: number(w["size"]) or 0):
        line = f"- `{w['cmd']}` at size {w['size']}: before {summary(w['before'])}"
        if w.get("after"):
            line += f"; after {summary(w['after'])}, output identical"
            if w.get("again") and w["again"] != w["before"]:
                line += f" (alternated with the code as it was: {summary(w['again'])})"
        print(line)
    for line in growth(works):
        print(line)
    big = max(works, key=lambda w: number(w["size"]) or 0)
    prof = [r for r in (big.get("profile") or {}).get("mine", []) if r["share"] < 0.9]   # not the entry point
    if prof:
        print(f"Where the time went at size {big['size']}: "
              + "; ".join(f"{r['func']} {r['share'] * 100:.0f}% ({r['ncalls']} calls)" for r in prof[:5]) + ".")
    if files:
        print(f"Changed: {', '.join(funcs)}. Cause and fix, one line each: [[fill: X cost Y because Z; now W]]")
        print(f"Guard: `{guard}` passes now and fails with each of {', '.join(files)} put back alone.")
    else:
        print("Diagnosis only, nothing changed. Cause, one line each: [[fill: X cost Y because Z; the fix and "
              "what it should cut]]")
    print("Not measured: [[fill: sizes, machines, cold starts or paths no workload here ran]]")
    print(f"\nPERF-GATE: done({len(works)} workloads, {'changed ' + str(len(files)) + ' files' if files else 'diagnosis'})")


def overview(repo):
    ledger = read_json(repo, LEDGER, {})
    works = ledger.get("workloads", [])
    if not works:
        print("nothing measured yet.")
    for w in works:
        print(f"`{w['cmd']}` size {w['size']}: before {summary(w['before'])}")
    files = changed_files(repo)
    if files:
        print(f"changed since the first measure: {', '.join(files)}")
    print('next: P --measure "<cmd>" --size <N> (two sizes), change one thing, P --gate --guard "<test cmd>"')
    return 0


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description="Measured before and after, aimed by a profile, held by a guard.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--measure", metavar="CMD", help="a workload command that prints its result")
    ap.add_argument("--size", help="the workload's size (rows, users, requests)")
    ap.add_argument("--runs", type=int, default=5, help="timed runs per workload")
    ap.add_argument("--gate", action="store_true", help="check the three stages")
    ap.add_argument("--guard", metavar="CMD", help="a test command that fails when the gain is taken out")
    ap.add_argument("--timeout", type=int, default=600, help="seconds per command")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo)
    if a.measure is not None:
        return measure(repo, a.measure, a.size, max(1, a.runs), a.timeout)
    if a.gate:
        return gate(repo, a.guard, a.timeout)
    return overview(repo)


if __name__ == "__main__":
    sys.exit(main())
