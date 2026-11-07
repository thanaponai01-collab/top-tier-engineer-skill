#!/usr/bin/env python3
"""
untangle.py - the history-ranked scope, the baseline and the behavior check behind `untangle`.

  untangle.py <repo>                       rank hotspots and co-change pairs from git history
  untangle.py <repo> --gate --run CMD ...  record the baseline (first call), then check the stages

Stage 1 (baseline): the test commands ran on the committed tree, before any code changed. Every
ranked hotspot and pair has a target/skip line, and every red test has an env/stale/bug line.
Stage 2 (untangle): every changed code file is a target or `also` serves one; every target has a
move line whose guard passes now and fails on the committed tree.
Stage 3 (same behavior): the same commands rerun; nothing green went red, no command ran fewer tests.

Stdlib only. State lives in <repo>/.untangle/ (state.json, notes.md).
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams  # noqa: E402

STATE = ".untangle"
CODE_EXT = {".py", ".js", ".cjs", ".mjs", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".kt", ".rb",
            ".php", ".cs", ".c", ".cc", ".cpp", ".h", ".hpp", ".swift", ".scala", ".sh", ".ps1"}
SKIP_DIRS = {".git", "node_modules", "vendor", "third_party", "dist", "build", "__pycache__",
             ".untangle", ".release", ".perf", ".evolve", ".latent", ".wire", ".structure",
             ".debug", ".features", ".threat", ".verify-state", ".blast", ".mistakes", ".formal"}
FIX = re.compile(r"\b(fix|fixes|fixed|bug|regression|hotfix|revert)\b", re.I)
KINDS = ("env", "stale", "bug")
MARKER = "untangle: known bug"


# ---------------------------------------------------------------- git and files

def sh(args, cwd, timeout=600, shell=False):
    # A wide terminal: pytest cuts each summary line to the terminal width (80 when piped), which
    # drops the failure message that groups reds into one slot.
    env = dict(os.environ, COLUMNS="2000")
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, shell=shell, env=env)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s"


def git(repo, *args):
    return sh(["git", *args], repo)


def is_code(path):
    parts = path.replace("\\", "/").split("/")
    if any(p in SKIP_DIRS for p in parts[:-1]):
        return False
    name = parts[-1]
    if name.endswith((".d.ts", ".min.js")):
        return False
    return os.path.splitext(name)[1].lower() in CODE_EXT


def is_test(path):
    p = path.replace("\\", "/").lower()
    return "/test" in "/" + p or p.split("/")[-1].startswith("test") or ".test." in p or "_test." in p


def head(repo):
    rc, out = git(repo, "rev-parse", "HEAD")
    return out.strip() if rc == 0 else None


def changed_since(repo, base):
    """Code-or-not paths that differ from `base`: committed, staged, unstaged and untracked."""
    _, diff = git(repo, "diff", "--name-only", base)
    _, new = git(repo, "ls-files", "--others", "--exclude-standard")
    paths = {p.strip() for p in (diff + "\n" + new).splitlines() if p.strip()}
    return sorted(p for p in paths if not p.startswith(STATE + "/"))


# ---------------------------------------------------------------- history

def tree_key(repo, base):
    """A hash of everything that differs from `base` (diff plus untracked files): equal keys mean
    the code under test is the same, so a guard or suite result can be reused."""
    import hashlib
    h = hashlib.sha1()
    h.update(git(repo, "diff", "--binary", base, "--", ".", f":(exclude){STATE}")[1].encode())
    for p in sorted(git(repo, "ls-files", "--others", "--exclude-standard")[1].splitlines()):
        if p.startswith(STATE + "/"):
            continue
        h.update(p.encode())
        try:
            with open(os.path.join(repo, p), "rb") as fh:
                h.update(fh.read())
        except OSError:
            pass
    return h.hexdigest()


def only_marker_added(repo, base, path):
    """True when the file's only change since `base` is added lines carrying the bug marker."""
    _, diff = git(repo, "diff", "-U0", base, "--", path)
    body = [l for l in diff.splitlines() if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    return bool(body) and all(l.startswith("+") and MARKER in l for l in body)


def history(repo, window=400, max_files=10, recent=100):
    rc, out = git(repo, "log", "--no-merges", f"-n{window}", "--format=@@%h\t%s", "--name-only")
    if rc != 0:
        return None
    rc, tracked = git(repo, "ls-files")
    alive = set(tracked.split("\n"))
    commits, cur = [], None
    for line in out.splitlines():
        if line.startswith("@@"):
            sha, _, subj = line[2:].partition("\t")
            cur = {"sha": sha, "subject": subj, "files": []}
            commits.append(cur)
        elif line.strip() and cur is not None:
            cur["files"].append(line.strip())
    churn, fixes, subjects = Counter(), Counter(), defaultdict(list)
    pairs, fresh = Counter(), set()
    for i, c in enumerate(commits):
        code = sorted({f for f in c["files"] if f in alive and is_code(f) and not is_test(f)})
        fix = bool(FIX.search(c["subject"]))
        for f in code:
            churn[f] += 1
            if i < recent:
                fresh.add(f)
            if fix:
                fixes[f] += 1
                subjects[f].append(f"{c['sha']} {c['subject']}")
        if 2 <= len(code) <= max_files:
            for i, a in enumerate(code):
                for b in code[i + 1:]:
                    pairs[(a, b)] += 1
    return {"commits": len(commits), "churn": churn, "fixes": fixes, "subjects": subjects,
            "pairs": pairs, "fresh": fresh, "recent": min(recent, len(commits))}


def fix_heavy(churn, fixes):
    """A file where a third or more of the commits are repairs: its skip must name a guard, not a
    reason. A busy file that mostly grows features (most commits not fixes) is not fix-heavy."""
    return fixes >= 2 and 3 * fixes >= churn


def rank(h, top=8, top_pairs=5, min_pair=3):
    """Fixes count double; a file nobody touched in the recent commits (an abandoned spike, a
    settled module) is not ranked however busy it once was."""
    live = [f for f in h["churn"] if f in h["fresh"] and h["churn"][f] >= 2]
    score = {f: h["churn"][f] + 2 * h["fixes"][f] for f in live}
    hot = sorted(score, key=lambda f: (-score[f], f))[:top]
    pairs = [(a, b, n) for (a, b), n in h["pairs"].most_common()
             if n >= min_pair and a in h["fresh"] and b in h["fresh"]][:top_pairs]
    return hot, pairs


def show_rank(h, hot, pairs):
    print(f"history: {h['commits']} commits read; files untouched in the last {h['recent']} are not ranked")
    print("HOTSPOTS (commits, fix commits):")
    for f in hot:
        heavy = "  FIX-HEAVY: a skip needs a guard" if fix_heavy(h["churn"][f], h["fixes"][f]) else ""
        print(f"  {f}  {h['churn'][f]} commits, {h['fixes'][f]} fixes{heavy}")
        for s in h["subjects"][f][:3]:
            print(f"      {s}")
    print("PAIRS that change together (commits):")
    for a, b, n in pairs:
        print(f"  {a} + {b}  {n}")
    if not hot:
        print("  (no file changed twice; history is too short to rank)")


# ---------------------------------------------------------------- test runs

def parse_run(out):
    """Counts, red test ids, and each red's failure message where the runner prints one, for
    pytest, node --test and unittest output."""
    ran, red, msgs = None, set(), {}
    m = re.findall(r"(\d+) passed", out)
    f = re.findall(r"(\d+) failed", out)
    e = re.findall(r"(\d+) errors?\b", out)
    if m or f:
        ran = sum(int(x) for x in (m[-1:] + f[-1:] + e[-1:]))
    for line in out.splitlines():
        s = line.strip()
        mp = re.match(r"(?:FAILED|ERROR) (\S+?\.\w+(?:::\S+)?)(?: - (.*)|$)", s)   # pytest summary
        if mp:
            red.add(mp.group(1))
            if mp.group(2):
                msgs[mp.group(1)] = mp.group(2).strip()
        mm = re.match(r"(?:FAIL|ERROR): (\S+) \(([^)]+)\)", s)                # unittest
        if mm:
            where = mm.group(2)
            red.add(where if where.endswith("." + mm.group(1)) else f"{where}.{mm.group(1)}")
        if s.startswith("not ok "):
            red.add(re.sub(r"^not ok \d+ - ", "", s))
    nm = re.findall(r"^\S*\s*(?:#|ℹ) tests (\d+)", out, re.M)
    if nm:
        ran = int(nm[-1])
    um = re.findall(r"^Ran (\d+) tests?", out, re.M)
    if um:
        ran = int(um[-1])
    return ran, sorted(red), msgs


def run_all(repo, cmds, timeout):
    res = []
    for cmd in cmds:
        rc, out = sh(cmd, repo, timeout=timeout, shell=True)
        ran, red, msgs = parse_run(out)
        res.append({"cmd": cmd, "rc": rc, "ran": ran, "red": red, "msgs": msgs,
                    "tail": out.strip().splitlines()[-3:]})
    return res


def ran_nothing(repo, r):
    """Why a baseline run cannot stand for the suite, or None. A baseline that ran no test would
    let every later red count as already red."""
    if r["ran"] == 0:
        return "ran 0 tests"
    if r["ran"] is None and r["rc"] != 0:
        return f"exited {r['rc']} and printed no test count"
    folders = [t for t in r["red"] if os.path.isdir(os.path.join(repo, t.rstrip("/\\")))]
    if folders:
        return f"ran the folder {folders[0]} as one test"
    return None


def same_message(a, b):
    """The common text of two failure messages, when one is the other cut short ('...'), else None.
    A cut that leaves under 20 characters says too little to group on."""
    a, b = a.rstrip(". "), b.rstrip(". ")
    short, long_ = sorted((a, b), key=len)
    return short if len(short) >= 20 and long_.startswith(short) else (a if a == b and a else None)


def red_keys(r):
    """Slot keys for one run's reds: reds in one file that fail with the same message share one,
    also when the runner cut some of the messages short."""
    groups = defaultdict(list)
    for t in sorted(r["red"], key=lambda t: len(r.get("msgs", {}).get(t) or "")):
        msg = (r.get("msgs", {}).get(t) or "").strip()
        if not msg.rstrip(". "):
            groups[(t, None)].append(t)
            continue
        where = t.split("::")[0]
        hit = next(((w, m) for (w, m) in groups if w == where and m and same_message(m, msg)), None)
        if hit:
            groups[hit].append(t)
        else:
            groups[(where, msg.rstrip(". ") if msg.endswith("...") else msg)].append(t)
    keys = {}
    for (where, msg), ids in groups.items():
        key = f"{r['cmd']} :: {where}::* ({msg})" if msg and len(ids) > 1 else f"{r['cmd']} :: {ids[0]}"
        keys[key] = ids
    return keys


# ---------------------------------------------------------------- notes

def notes_path(repo):
    return os.path.join(repo, STATE, "notes.md")


def read_notes(repo):
    try:
        with open(notes_path(repo), encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def lines_for(text, kind, keys=None):
    """{key: value} for lines `- <kind> <key>: <value>`. Keys that may hold ': ' (test names) are
    looked up exactly; the last line for a key wins."""
    out = {}
    if keys is not None:
        for k in keys:
            for m in re.finditer(rf"^- {kind} {re.escape(k)}: (.*)$", text, re.M):
                out[k] = m.group(1).strip()
        return out
    for m in re.finditer(rf"^- {kind} (.+?): (.*)$", text, re.M):
        out[m.group(1).strip()] = m.group(2).strip()
    return out


def append_slots(repo, slots):
    text = read_notes(repo)
    new = [s for s in slots if s.rsplit(": [[fill", 1)[0] + ":" not in text]
    if not new:
        return
    os.makedirs(os.path.join(repo, STATE), exist_ok=True)
    with open(notes_path(repo), "a", encoding="utf-8", newline="\n") as fh:
        if not text:
            fh.write("# untangle notes\n\n")
        fh.write("\n".join(new) + "\n")


def filled(v):
    return bool(v) and "[[fill" not in v


# ---------------------------------------------------------------- state

def state_path(repo):
    return os.path.join(repo, STATE, "state.json")


def load_state(repo):
    try:
        with open(state_path(repo), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def save_state(repo, st):
    os.makedirs(os.path.join(repo, STATE), exist_ok=True)
    with open(state_path(repo), "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1)


def take_baseline(repo, cmds, args):
    base = head(repo)
    if not base:
        return None, "no commit to stand on: commit the code as it is first"
    dirty = [p for p in changed_since(repo, base)]
    if dirty:
        return None, ("the baseline must be the code as committed, but these differ from HEAD: "
                      + ", ".join(dirty[:8]) + ". Commit or stash them, then run again")
    runs = run_all(repo, cmds, args.timeout)
    bad = [(r, ran_nothing(repo, r)) for r in runs]
    bad = [f"`{r['cmd']}` {why}" for r, why in bad if why]
    if bad:
        return None, ("; ".join(bad) + ". Fix the command (nothing was recorded), then run again")
    h = history(repo, args.window, recent=args.recent)
    hot, pairs = rank(h, args.top)
    st = {"base": base, "cmds": cmds, "baseline": runs, "hotspots": hot,
          "hot_info": {f: [h["churn"][f], h["fixes"][f]] for f in hot},
          "pairs": [[a, b, n] for a, b, n in pairs], "cache": {}}
    save_state(repo, st)
    return st, None


# ---------------------------------------------------------------- guards

def guard_red_on_base(repo, base, cmd, timeout):
    """Run the guard in a worktree of `base`, with the files the command names copied in."""
    tmp = tempfile.mkdtemp(prefix="untangle-guard-")
    wt = os.path.join(tmp, "wt")
    rc, out = git(repo, "worktree", "add", "--detach", wt, base)
    if rc != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        return None, out.strip()[-200:]
    try:
        for tok in re.split(r"[\s'\"]+", cmd):
            tok = tok.split("::")[0]
            src = os.path.join(repo, tok)
            if tok and os.path.isfile(src) and not os.path.isabs(tok):
                dst = os.path.join(wt, tok)
                os.makedirs(os.path.dirname(dst) or wt, exist_ok=True)
                shutil.copy2(src, dst)
        rc, out = sh(cmd, wt, timeout=timeout, shell=True)
        return rc, out.strip().splitlines()[-1:] if out.strip() else []
    finally:
        git(repo, "worktree", "remove", "--force", wt)
        shutil.rmtree(tmp, ignore_errors=True)


LAST_FIXES = 5


def recent_fixes(repo, base, path, window):
    """The last LAST_FIXES fix commits that touched `path`, newest first, as of `base`."""
    _, out = git(repo, "log", "--no-merges", f"-n{window}", "--format=%h\t%s", base, "--", path)
    shas = [l.split("\t")[0] for l in out.splitlines() if "\t" in l and FIX.search(l.split("\t", 1)[1])]
    return shas[:LAST_FIXES]


def guard_with_fix_undone(repo, base, path, sha, cmd, timeout):
    """Run the guard on the current tree with one past fix to `path` reverted, in a worktree of
    `base` with every changed file copied in, so the person's tree is never touched.
    Returns 'red', 'green', or 'n/a' when that fix no longer reverts cleanly."""
    _, patch = git(repo, "diff", f"{sha}^", sha, "--", path)
    if not patch.strip():
        return "n/a"
    tmp = tempfile.mkdtemp(prefix="untangle-revert-")
    wt = os.path.join(tmp, "wt")
    rc, _ = git(repo, "worktree", "add", "--detach", wt, base)
    if rc != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        return "n/a"
    try:
        for p in changed_since(repo, base):
            src, dst = os.path.join(repo, p), os.path.join(wt, p)
            if os.path.isfile(src):
                os.makedirs(os.path.dirname(dst) or wt, exist_ok=True)
                shutil.copy2(src, dst)
            elif os.path.exists(dst):
                os.remove(dst)
        pfile = os.path.join(tmp, "fix.diff")
        with open(pfile, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(patch if patch.endswith("\n") else patch + "\n")
        if git(wt, "apply", "-R", pfile)[0] != 0:
            return "n/a"
        rc, _ = sh(cmd, wt, timeout=timeout, shell=True)
        return "green" if rc == 0 else "red"
    finally:
        git(repo, "worktree", "remove", "--force", wt)
        shutil.rmtree(tmp, ignore_errors=True)


def skip_guard_misses(repo, st, key, unit, gcmd, excused, args):
    """Past fixes to a skipped fix-heavy file whose undoing the guard does not notice. A skip says
    the repeated fixes are already pinned; this checks that claim fix by fix."""
    misses = []
    for sha in recent_fixes(repo, st["base"], unit, args.window):
        if any(e.startswith(sha) or sha.startswith(e) for e in excused):
            continue
        res = cached(st, key, f"revert:{sha}:{unit}:{gcmd}",
                     lambda: guard_with_fix_undone(repo, st["base"], unit, sha, gcmd, args.timeout))
        if res == "green":
            misses.append(sha)
    return misses


# ---------------------------------------------------------------- the gate

def cached(st, key, what, fn):
    """Reuse a guard or suite result while the code under test is unchanged."""
    slot = f"{what}@{key}"
    if slot not in st.setdefault("cache", {}):
        st["cache"][slot] = fn()
    return st["cache"][slot]


def check_guard(repo, st, key, gcmd, timeout, need_red_on_base=True):
    """None when the guard holds, else what is wrong with it."""
    rc = cached(st, key, f"now:{gcmd}", lambda: sh(gcmd, repo, timeout=timeout, shell=True)[0])
    if rc != 0:
        return f"fails on the changed tree: {gcmd}"
    if not need_red_on_base:
        return None
    res = cached(st, key, f"base:{gcmd}",
                 lambda: list(guard_red_on_base(repo, st["base"], gcmd, timeout)))
    if res[0] is None:
        return f"could not check out the baseline ({res[1]})"
    if res[0] == 0:
        return f"also passes on the committed tree, so it would not catch the tangle coming back: {gcmd}"
    return None


def names_file(repo, gcmd, stem):
    """Some file the guard command names mentions `stem` (the hotspot's module name)."""
    for tok in re.split(r"[\s'\"]+", gcmd):
        p = os.path.join(repo, tok.split("::")[0])
        if tok and os.path.isfile(p):
            try:
                with open(p, encoding="utf-8", errors="replace") as fh:
                    if stem in fh.read():
                        return True
            except OSError:
                pass
    return False


def marker_near(repo, evidence):
    """The bug's file:line (the first one in the evidence that exists) and whether a MARKER
    comment sits within 3 lines of it."""
    for path, line in re.findall(r"([\w./\\-]+\.\w+):(\d+)", evidence):
        p = os.path.join(repo, path)
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        n = int(line)
        near = lines[max(0, n - 4):n + 3]
        return f"{path}:{line}", any(MARKER in l for l in near)
    return None, False


def gate(repo, args):
    st = load_state(repo)
    cmds = args.run or []
    if st is None:
        if not cmds:
            print("STAGE 1 OPEN: no baseline. Run `--gate --run \"<test cmd>\"` on the committed tree,"
                  " before changing any code")
            return 1
        st, err = take_baseline(repo, cmds, args)
        if err:
            print("STAGE 1 OPEN: " + err)
            return 1
        print(f"baseline recorded at {st['base'][:10]}: " + "; ".join(
            f"{r['cmd']} -> rc {r['rc']}, {r['ran']} tests, {len(r['red'])} red" for r in st["baseline"]))
    elif cmds and cmds != st["cmds"]:
        print("STAGE 3 OPEN: --run differs from the baseline's commands; use the same: "
              + " | ".join(st["cmds"]))
        return 1

    hot, pairs, info = st["hotspots"], st["pairs"], st.get("hot_info", {})
    pair_keys = [f"{a} + {b}" for a, b, _ in pairs]
    groups = {}
    for r in st["baseline"]:
        groups.update(red_keys(r))
        if r["rc"] != 0 and not r["red"]:
            groups[f"{r['cmd']} :: (exit {r['rc']})"] = []
    reds = list(groups)
    append_slots(repo, [f"- hotspot {f}: [[fill: target: <commits that show the cost> | skip: <why>"
                        + (" | guard: <cmd whose tests cover the repeated fixes>" if fix_heavy(*info.get(f, [0, 0])) else "")
                        + "]]" for f in hot]
                 + [f"- pair {k}: [[fill: target: <why> | skip: <why>]]" for k in pair_keys]
                 + [f"- red {r}: [[fill: env | stale | bug: <evidence, file:line>]]" for r in reds])
    text = read_notes(repo)
    key = tree_key(repo, st["base"])
    problems = []

    # stage 1: scope and the reds
    marks = {**{f: v for f, v in lines_for(text, "hotspot", hot).items()},
             **{k: v for k, v in lines_for(text, "pair", pair_keys).items()}}
    units = {}   # target unit (a hotspot, or a pair as one) -> its files
    for unit in hot + pair_keys:
        v = marks.get(unit, "")
        m = re.match(r"(target|skip):\s*(\S.*)", v) if filled(v) else None
        kind = "hotspot" if unit in hot else "pair"
        if not m:
            problems.append((1, f"{kind} {unit}: say `target: <commits>` or `skip: <why>`"))
        elif m.group(1) == "target":
            units[unit] = unit.split(" + ")
        elif kind == "hotspot" and fix_heavy(*info.get(unit, [0, 0])):
            churn, fixes = info[unit]
            parts = [p.strip() for p in v.split("|")]
            gcmd = next((p.split(":", 1)[1].strip() for p in parts if p.startswith("guard:")), "")
            excused = [p.split(":", 2)[1].strip() for p in parts
                       if p.startswith("unguarded:") and len(p.split(":", 2)) == 3 and p.split(":", 2)[2].strip()]
            if not gcmd:
                problems.append((1, f"hotspot {unit}: {fixes} of its {churn} commits are fixes; a skip "
                                    f"needs `| guard: <cmd>` whose tests cover them, or make it a target"))
                continue
            stem = os.path.splitext(os.path.basename(unit))[0]
            if not names_file(repo, gcmd, stem):
                problems.append((1, f"hotspot {unit}: the skip's guard names no test file that mentions {stem}"))
                continue
            bad = check_guard(repo, st, key, gcmd, args.timeout, need_red_on_base=False)
            if bad:
                problems.append((1, f"hotspot {unit}: the skip's guard {bad}"))
                continue
            misses = skip_guard_misses(repo, st, key, unit, gcmd, excused, args)
            if misses:
                problems.append((1, f"hotspot {unit}: the skip's guard still passes with fix "
                                    f"{', '.join(misses)} undone, so it does not pin the repeated fixes. "
                                    f"Add a test that catches it, make the file a target, or add "
                                    f"`| unguarded: <sha>: <why it needs no test>`"))
    red_lines = lines_for(text, "red", reds)
    bug_files = set()
    for r in reds:
        v = red_lines.get(r, "")
        m = re.match(rf"({'|'.join(KINDS)}):\s*(\S.*)", v) if filled(v) else None
        if not m:
            problems.append((1, f"red {r}: say env, stale or bug, with its evidence"))
        elif m.group(1) == "bug":
            where, ok = marker_near(repo, m.group(2))
            if not where:
                problems.append((1, f"red {r}: a bug needs the file:line of the fault"))
            elif not ok:
                problems.append((1, f"red {r}: put a `{MARKER}: <the symptom>` comment within 3 lines "
                                    f"of {where}, where the next person debugging will look"))
            else:
                bug_files.add(where.rsplit(":", 1)[0].replace("\\", "/"))

    # stage 2: every change serves a target; every target's move is guarded
    changed = changed_since(repo, st["base"])
    code_changed = [p for p in changed if is_code(p) and not is_test(p)]
    target_files = {f for fs in units.values() for f in fs}
    also = lines_for(text, "also")
    # a targeted pair takes one move for both files; its files need no move of their own
    paired = {f for u, fs in units.items() if " + " in u for f in fs}
    move_units = {u: fs for u, fs in units.items() if " + " in u or u not in paired}
    moves = lines_for(text, "move", list(move_units))
    for p in code_changed:
        if p in target_files or (p in bug_files and only_marker_added(repo, st["base"], p)):
            continue
        v = also.get(p, "")
        m = re.match(r"serves (.+)", v)
        if not m or not any(t in m.group(1) for t in target_files):
            problems.append((2, f"{p} changed but is no target: add `- also {p}: serves <target>`"
                                f" or leave it alone"))
    for unit in sorted(move_units):
        files = move_units[unit]
        touched = [f for f in files if f in code_changed]
        v = moves.get(unit, "")
        if not filled(v):
            problems.append((2, f"move {unit}: say what changed and its guard, or `not moved: <why>`"))
            continue
        if v.startswith("not moved:"):
            if touched:
                problems.append((2, f"move {unit}: says not moved but {touched[0]} changed"))
            continue
        if not touched:
            problems.append((2, f"move {unit}: names no change ({', '.join(files)} unchanged); "
                                f"say `not moved: <why>`"))
            continue
        g = re.search(r"\|\s*guard:\s*(.+)$", v)
        if not g:
            problems.append((2, f"move {unit}: add `| guard: <cmd>` or `| guard: none: <why>`"))
            continue
        gcmd = g.group(1).strip()
        if gcmd.startswith("none:"):
            continue
        bad = check_guard(repo, st, key, gcmd, args.timeout)
        if bad:
            problems.append((2, f"guard for {unit} {bad}"))

    if not changed and units:
        problems.append((2, "nothing changed yet"))

    # stage 3: the suite reruns only once the stages before it hold, and not again on the same code
    after = None
    if changed and not problems:
        after = cached(st, key, "suite", lambda: run_all(repo, st["cmds"], args.timeout))
    elif changed:
        problems.append((3, "the tests rerun once stages 1 and 2 hold"))
    for b, a in zip(st["baseline"], after or []):
        newly = sorted(set(a["red"]) - set(b["red"]))
        if newly:
            problems.append((3, f"{b['cmd']}: green at the baseline, red now: " + ", ".join(newly[:6])))
        if b["rc"] == 0 and a["rc"] != 0 and not newly:
            problems.append((3, f"{b['cmd']}: exited 0 at the baseline, {a['rc']} now"))
        if b["ran"] is not None and (a["ran"] or 0) < b["ran"]:
            problems.append((3, f"{b['cmd']}: ran {a['ran']} tests, the baseline ran {b['ran']}"))
    save_state(repo, st)

    if problems:
        for s, msg in sorted(problems):
            print(f"STAGE {s} OPEN: {msg}")
        return 1
    answer(st, text, move_units, moves, changed, after, red_lines, reds)
    return 0


def answer(st, text, units, moves, changed, after, red_lines, reds):
    bugs = [r for r in reds if red_lines.get(r, "").startswith("bug")]
    print("\nANSWER")
    if bugs:
        print("Real faults found, not fixed (they change behavior); each is marked in the code:")
        for r in bugs:
            print(f"  - {r}: {red_lines[r][4:].strip()}")
    print("Untangled:" if units else "Nothing here needs untangling: every ranked hotspot was skipped.")
    for u in sorted(units):
        print(f"  - {u}: {moves.get(u, '')}")
    skips = {**lines_for(text, "hotspot", st["hotspots"]),
             **lines_for(text, "pair", [f"{a} + {b}" for a, b, _ in st["pairs"]])}
    left = [(k, v) for k, v in skips.items() if v.startswith("skip")]
    if left:
        print("Left alone:")
        for k, v in left:
            print(f"  - {k}: {v[5:].strip()}")
    for b, a in zip(st["baseline"], after or st["baseline"]):
        print(f"Tests `{b['cmd']}`: {b['ran']} ran, {len(b['red'])} red before; "
              f"{a['ran']} ran, {len(a['red'])} red after")
    print(f"\nUNTANGLE-GATE: done ({len(units)} targets, {len(changed)} files changed)")


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description="Untangle where history says changes hurt.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--gate", action="store_true", help="check the three stages")
    ap.add_argument("--run", action="append", metavar="CMD", help="a test command (repeatable)")
    ap.add_argument("--top", type=int, default=8, help="hotspots to rank (default 8)")
    ap.add_argument("--window", type=int, default=400, help="commits of history to read")
    ap.add_argument("--recent", type=int, default=100,
                    help="a file untouched in this many latest commits is not ranked (default 100)")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per command")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo)
    if git(repo, "rev-parse", "--git-dir")[0] != 0:
        print("untangle needs git: the history is how it finds where changes hurt")
        return 2
    if a.gate:
        return gate(repo, a)
    h = history(repo, a.window, recent=a.recent)
    hot, pairs = rank(h, a.top)
    show_rank(h, hot, pairs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
