#!/usr/bin/env python3
"""debug.py - the mechanical side of the debug-protocol skill.

A model that reads the code well names the right cause most of the time, then stops at "I saw the
bad value there". This keeps the two things it skips: the picture of the code as it was when the
failure was reproduced, and the run with only the cause taken out. Every command runs in a
throwaway copy, so probes never touch the person's tree.

  D --repro CMD --wrong TEXT --right TEXT
                           run CMD on the code as it is now (kept as .debug/before/ the first time)
                           and record that its output shows TEXT wrong and not TEXT right
  D --prove FILE:LINE[-END] --as TEXT --why HYPOTHESIS
                           one experiment: those lines replaced by TEXT in a copy of the before
                           code, CMD run again. Proven when the wrong text is gone and the right
                           one shows. Every try is kept in .debug/experiments, dead ends too.
                           The first try also runs the test suite on the before code and records
                           whether it passes and whether any test enters the cause's function
  D --gate [--regress CMD] check the stages and print every problem with its fix:
    1 reproduce  the failure shows on demand on the code as it was
    2 prove      one experiment took only the cause out and the failure went away
    3 leave      no fix: the tree is back to the code as it was (probe edits gone)
                 a fix: it is in the cause's file, CMD shows the right text, and the regress
                 command passes now and fails with the cause put back

`D` is `python debug.py <repo>`. Stdlib only.
"""
import argparse, ast, hashlib, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _encoding import utf8_streams  # noqa: E402

STATE = ".debug"
BEFORE = f"{STATE}/before"
LEDGER = f"{STATE}/state.json"
# Folders that hold tools' state or caches, never the product: not copied, not compared.
NOT_PRODUCT = {".git", "__pycache__", "node_modules", ".venv", "venv", STATE, ".wire", ".latent",
               ".features", ".verify-state-cache", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".threat", ".evolve", ".perf"}
NOT_PRODUCT_FILES = {".verify-state.json"}
BASH = shutil.which("bash")
BUDGET = 5
NO_TESTS = re.compile(r"^Ran 0 tests\b|\bno tests ran\b", re.MULTILINE | re.IGNORECASE)

TRACER = r'''import atexit, os, sys, threading
_dbg_root = os.path.normcase(os.path.abspath(os.environ.get("DEBUG_ROOT", ".")))
_dbg_seen = set()
def _dbg_profile(frame, event, arg):
    if event == "call":
        _dbg_seen.add((frame.f_code.co_filename, frame.f_code.co_firstlineno))
def _dbg_dump():
    sys.setprofile(None)
    threading.setprofile(None)
    try:
        with open(os.environ["DEBUG_CALL_LOG"], "a", encoding="utf-8") as fh:
            for f, line in list(_dbg_seen):
                p = os.path.normcase(os.path.abspath(f))
                if p.startswith(_dbg_root + os.sep):
                    fh.write(f"{p}\t{line}\n")
    except Exception:
        pass
sys.setprofile(_dbg_profile)
threading.setprofile(_dbg_profile)
atexit.register(_dbg_dump)
'''


# ---------------- files and runs -------------------------------------------------
def rel(path, root):
    return os.path.relpath(path, root).replace(os.sep, "/")


def product_files(root):
    """{rel path: sha} for every file that is the product, not a tool's state."""
    out = {}
    for d, subdirs, names in os.walk(root):
        subdirs[:] = sorted(s for s in subdirs if s not in NOT_PRODUCT)
        for n in sorted(names):
            if n in NOT_PRODUCT_FILES or n.endswith(".pyc"):
                continue
            p = os.path.join(d, n)
            with open(p, "rb") as fh:
                out[rel(p, root)] = hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()[:16]
    return out


def copy_tree(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*NOT_PRODUCT, "*.pyc"))


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        return fh.read().splitlines(keepends=True)


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


def run_in(root, cmd, timeout, trace=False):
    """Run CMD in ROOT (already a throwaway copy). (exit, output, {(file, first line)} entered)."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env["PYTHONPATH"] = os.pathsep.join([root] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    hook = log = None
    if trace:
        hook = tempfile.mkdtemp(prefix="debug-hook-")
        with open(os.path.join(hook, "sitecustomize.py"), "w", encoding="utf-8") as fh:
            fh.write(TRACER)
        log = os.path.join(hook, "calls.txt")
        env.update(DEBUG_ROOT=root, DEBUG_CALL_LOG=log, PYTHONPATH=hook + os.pathsep + env["PYTHONPATH"])
    # Agents write commands in the shell they use (`VAR=x cmd`, `&&`), so prefer bash.
    argv = [BASH, "-c", cmd] if BASH else cmd
    try:
        p = subprocess.run(argv, cwd=root, shell=not BASH, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env)
        code, text = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        code, text = "timeout", "timed out"
    entered = set()
    if log:
        try:
            with open(log, encoding="utf-8") as fh:
                for row in fh:
                    path, _, line = row.rstrip("\n").rpartition("\t")
                    if line.isdigit():
                        entered.add((rel(path, os.path.normcase(os.path.abspath(root))), int(line)))
        except OSError:
            pass
        shutil.rmtree(hook, ignore_errors=True)
    return code, text.replace(root, "<repo>"), entered


def run_copy(src, cmd, timeout, edits=None, trace=False):
    """Run CMD in a throwaway copy of SRC with EDITS ({rel: text}) applied first."""
    tmp = tempfile.mkdtemp(prefix="debug-")
    try:
        root = os.path.join(tmp, "repo")
        copy_tree(src, root)
        for r, text in (edits or {}).items():
            with open(os.path.join(root, *r.split("/")), "w", encoding="utf-8", newline="") as fh:
                fh.write(text)
        return run_in(root, cmd, timeout, trace)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def tail(text, n=4):
    return [ln[:200] for ln in text.splitlines() if ln.strip()][-n:]


def shows(text, wrong, right):
    """(wrong text seen, right text seen)."""
    return wrong in text, right in text


# ---------------- stage 1: reproduce ------------------------------------------------
def repro(repo, cmd, wrong, right, timeout):
    if not (cmd and wrong and right):
        print('REPRO: give all three: D --repro "<cmd that shows it>" --wrong "<text of the bad output>" '
              '--right "<what it should show, from the spec or the data>"')
        return 2
    before = os.path.join(repo, BEFORE)
    if not os.path.isdir(before):
        copy_tree(repo, before)   # the code as it was when the failure was reproduced, kept for good
    ledger = read_json(repo, LEDGER, {})
    code, out, _ = run_copy(before, cmd, timeout)
    w, r = shows(out, wrong, right)
    ledger["repro"] = {"cmd": cmd, "wrong": wrong, "right": right, "exit": code, "tail": tail(out),
                       "wrong_seen": w, "right_seen": r}
    save(repo, ledger)
    print(f"REPRO: exit {code}  {cmd}")
    print("".join(f"  | {ln}\n" for ln in tail(out, 6)), end="")
    if w and not r:
        print(f"REPRO: reproduced: shows {wrong!r}, not {right!r}. The code as it is now is kept in {BEFORE}/.")
        print('next: localize (run what you like), then D --prove FILE:LINE --as "<the line without the cause>" '
              '--why "<one sentence that could be wrong>"')
        return 0
    print(f"REPRO: not reproduced: {'the wrong text never showed' if not w else 'the right text showed too'}. "
          "Change the command or the texts so the output shows the failure and not the right answer.")
    return 1


# ---------------- stage 2: prove ----------------------------------------------------
def enclosing_function(path, line):
    """(qualified name, first line as a running function reports it) of the innermost function
    holding LINE, or (None, None) for module-level code or a file that is not Python."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            tree = ast.parse(fh.read())
    except (SyntaxError, ValueError, OSError):
        return None, None
    best = (None, None, -1)

    def walk(node, prefix):
        nonlocal best
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}{child.name}"
                end = getattr(child, "end_lineno", child.lineno)
                first = min([child.lineno] + [d.lineno for d in child.decorator_list])
                if first <= line <= end and not isinstance(child, ast.ClassDef) and first > best[2]:
                    best = (name, first, first)
                walk(child, name + ".")
    walk(tree, "")
    return best[0], best[1]


def default_tests(root):
    if os.path.isfile(os.path.join(root, "conftest.py")) or os.path.isfile(os.path.join(root, "pytest.ini")):
        return "python -m pytest -q"
    if os.path.isdir(os.path.join(root, "tests")):
        return "python -m unittest discover -s tests"
    for d, subdirs, names in os.walk(root):
        subdirs[:] = [s for s in subdirs if s not in NOT_PRODUCT]
        if any(re.match(r"^(test_.+|.+_test)\.py$", n) for n in names):
            return "python -m unittest discover"
    return None


def suite_receipt(repo, tests_cmd, timeout):
    """The test suite run once on the before code, under a call tracer."""
    before = os.path.join(repo, BEFORE)
    cmd = tests_cmd or default_tests(before)
    if not cmd:
        return {"cmd": None}
    code, out, entered = run_copy(before, cmd, timeout, trace=True)
    m = re.search(r"\bRan (\d+) tests?\b|(\d+) passed", out)
    return {"cmd": cmd, "exit": code, "tail": tail(out, 3), "ran": int(m.group(1) or m.group(2)) if m else None,
            "no_tests": bool(NO_TESTS.search(out)), "entered": sorted(f"{f}:{ln}" for f, ln in entered)}


def parse_where(where):
    m = re.match(r"^(.+?):(\d+)(?:-(\d+))?$", where.strip())
    if not m:
        return None
    start, f = int(m.group(2)), m.group(1).replace("\\", "/")
    return (f[2:] if f.startswith("./") else f), start, int(m.group(3) or start)


def prove(repo, where, as_text, why, tests_cmd, timeout):
    ledger = read_json(repo, LEDGER, {})
    rp = ledger.get("repro")
    if not rp or not (rp["wrong_seen"] and not rp["right_seen"]):
        print('PROVE: reproduce first: D --repro "<cmd>" --wrong "<text>" --right "<text>"')
        return 2
    loc = parse_where(where or "")
    if not loc or as_text is None or not (why or "").strip():
        print('PROVE: give the place, the replacement and the hypothesis: D --prove FILE:LINE[-END] '
              '--as "<the code without the cause>" --why "<X fails because Y>"')
        return 2
    f, start, end = loc
    path = os.path.join(repo, BEFORE, *f.split("/"))
    if not os.path.isfile(path):
        print(f"PROVE: {f} is not in the code as it was ({BEFORE}/). Name a file relative to the repo.")
        return 2
    lines = read_lines(path)
    if start < 1 or end > len(lines) or end < start:
        print(f"PROVE: {f} has {len(lines)} lines; {start}-{end} is not a range in it.")
        return 2
    if rp["right"].strip() and rp["right"].strip() in as_text:
        print(f"PROVE: the replacement spells the right answer {rp['right']!r} itself. That proves the output "
              "can be typed, not where it goes wrong. Take out only the cause.")
        return 2
    old = "".join(lines[start - 1:end])
    nl = "\r\n" if old.endswith("\r\n") else "\n"
    indent = re.match(r"[ \t]*", old).group(0)
    new = [ln if (not ln.strip() or ln[:1] in " \t") else indent + ln for ln in as_text.split("\n")] \
        if as_text else []
    text = "".join(lines[:start - 1]) + "".join(ln + nl for ln in new) + "".join(lines[end:])
    code, out, _ = run_copy(os.path.join(repo, BEFORE), rp["cmd"], timeout, edits={f: text})
    w, r = shows(out, rp["wrong"], rp["right"])
    verdict = "proven" if (r and not w) else "refuted"
    func, first = enclosing_function(path, start)
    exp = {"n": len(ledger.get("experiments", [])) + 1, "why": why.strip(), "file": f, "start": start,
           "end": end, "was": old.rstrip("\r\n"), "as": as_text, "exit": code, "tail": tail(out),
           "verdict": verdict, "function": func, "first": first}
    ledger.setdefault("experiments", []).append(exp)
    if "suite" not in ledger or (tests_cmd and ledger["suite"].get("cmd") != tests_cmd):
        ledger["suite"] = suite_receipt(repo, tests_cmd, timeout)
    save(repo, ledger)
    print(f"EXPERIMENT {exp['n']}: {why.strip()}")
    print(f"  with the cause    ({f}:{start}: {old.strip()[:80]}): exit {rp['exit']}, shows {rp['wrong']!r}")
    print(f"  without the cause ({(as_text.strip() or '<removed>')[:80]}): exit {code}, "
          f"{'shows ' + repr(rp['right']) if r else 'no ' + repr(rp['right'])}"
          f"{', still shows ' + repr(rp['wrong']) if w else ''}")
    print("".join(f"  | {ln}\n" for ln in tail(out, 4)), end="")
    print(f"PROVE: {verdict}" + ("" if verdict == "proven" else ". Kept in the table as a dead end"))
    print("next: D --gate")
    return 0 if verdict == "proven" else 1


# ---------------- stage 3: leave ----------------------------------------------------
def verify_paths(repo):
    """{section: [path entries]} from VERIFY.md (verify-loop's map of checks)."""
    out, name = {}, None
    try:
        text = open(os.path.join(repo, "VERIFY.md"), encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            name = m.group(1)
            out[name] = []
            continue
        m = re.match(r"^\s*-\s*path:\s*(.+)$", line)
        if m and name:
            out[name] += [p.strip().strip("`").rstrip("/") for p in m.group(1).split(",") if p.strip()]
    return out


def regress_receipt(repo, cmd, cause_files, timeout):
    """CMD on the tree now (must pass) and on the tree now with the cause files put back (must fail)."""
    before = os.path.join(repo, BEFORE)
    now_code, now_out, _ = run_copy(repo, cmd, timeout)
    edits = {}
    for f in cause_files:
        with open(os.path.join(before, *f.split("/")), encoding="utf-8", errors="replace", newline="") as fh:
            edits[f] = fh.read()
    back_code, back_out, _ = run_copy(repo, cmd, timeout, edits=edits)
    return {"cmd": cmd, "files": cause_files, "shas": product_files(repo),
            "now": {"exit": now_code, "tail": tail(now_out, 3), "no_tests": bool(NO_TESTS.search(now_out))},
            "cause_back": {"exit": back_code, "tail": tail(back_out, 3), "no_tests": bool(NO_TESTS.search(back_out))}}


def gate(repo, regress_cmd, timeout):
    ledger = read_json(repo, LEDGER, {})
    problems = {1: [], 2: [], 3: []}
    print('D = python "' + os.path.abspath(__file__) + '" ' + repo)
    rp = ledger.get("repro")
    if not rp:
        problems[1].append('nothing reproduced. Before changing any code: D --repro "<cmd>" --wrong "<text of the '
                           'bad output>" --right "<what it should show>" (runs in a throwaway copy)')
    elif not (rp["wrong_seen"] and not rp["right_seen"]):
        problems[1].append("the recorded run did not show the failure. Run D --repro again with a command or "
                           "texts that do")
    exps = ledger.get("experiments", [])
    proven = [e for e in exps if e["verdict"] == "proven"]
    cause = proven[-1] if proven else None
    if not problems[1] and not cause:
        if len(exps) >= BUDGET:
            problems[2].append(f"{len(exps)} experiments, none proven: you are past the budget. Report what is "
                               "ruled out (the table D --gate prints), what is open and the next experiment")
        else:
            problems[2].append('no experiment took the cause out and made the failure go away. Localize (where is the '
                               'value first wrong?), then D --prove FILE:LINE --as "<that code without the cause>" '
                               '--why "<X fails because Y>"')
        refuted = [e["file"] for e in exps if e["verdict"] == "refuted"]
        if len(refuted) >= 2 and refuted[-1] == refuted[-2]:
            problems[2].append(f"two refuted experiments in {refuted[-1]}: your model of the system is off. "
                               "Re-observe where the value first goes wrong before a third try there")

    # stage 3: what the tree looks like now
    before = os.path.join(repo, BEFORE)
    fix = None
    if os.path.isdir(before):
        was, now = product_files(before), product_files(repo)
        changed = sorted(f for f in was if now.get(f) != was[f])
        added = sorted(f for f in now if f not in was)
        fix = bool(changed)
        if fix and not cause:
            problems[3].append(f"{', '.join(changed[:4])} differ from the code you reproduced on, before any cause "
                               "was proven. Restore them: no fixing while diagnosing")
        elif fix:
            cause_files = sorted({e["file"] for e in proven if e["file"] in changed}) or [cause["file"]]
            if cause["file"] not in changed:
                problems[3].append(f"the fix changes {', '.join(changed[:4])} but the proven cause is in "
                                   f"{cause['file']}:{cause['start']}. Fix it where it starts, or restore "
                                   "those files (diagnosis only)")
            code, out, _ = run_copy(repo, rp["cmd"], timeout)
            w, r = shows(out, rp["wrong"], rp["right"])
            if w or not r:
                problems[3].append(f"`{rp['cmd']}` on the fixed code {'still shows ' + repr(rp['wrong']) if w else 'does not show ' + repr(rp['right'])}"
                                   f" (last: {tail(out, 1)[0] if tail(out, 1) else 'no output'})")
            rr = ledger.get("regress")
            cmd = regress_cmd or (rr or {}).get("cmd")
            if not cmd:
                problems[3].append('no regression check. Write one that runs the minimal reproduction through the real '
                                   'entry point, then: D --gate --regress "<test command>"; it must fail with the '
                                   'cause put back and pass now')
            else:
                if regress_cmd or not rr or rr.get("shas") != now or rr.get("files") != cause_files:
                    rr = ledger["regress"] = regress_receipt(repo, cmd, cause_files, timeout)
                    save(repo, ledger)
                n, b = rr["now"], rr["cause_back"]
                if n["exit"] != 0 or n["no_tests"]:
                    problems[3].append(f"`{cmd}` does not pass on the fixed code (exit {n['exit']}"
                                       f"{', ran no tests' if n['no_tests'] else ''}): {' / '.join(n['tail'][-1:])}")
                if b["exit"] in (0, "timeout") or b["no_tests"]:
                    problems[3].append(f"`{cmd}` passes with {', '.join(cause_files)} put back as it was: it cannot "
                                       "see this bug. Make it check the value the spec says, through the entry point")
            paths = verify_paths(repo)
            if paths is not None and not any(cause["file"] == p or cause["file"].startswith(p + "/")
                                             for ps in paths.values() for p in ps):
                problems[3].append(f"VERIFY.md maps no check over {cause['file']}, so verify-loop will not keep it "
                                   "proven. Append (existing sections stay as they are):\n      ## <feature>\n"
                                   f"      - path: {cause['file']}\n      - test: `{cmd or '<regression command>'}`\n"
                                   "      - oracle: <the spec file>\n      - fail-signal: <text the check prints on the bug>")
        ledger["_changed"], ledger["_added"] = changed, added

    names = {1: "reproduce: the failure shows on demand", 2: "prove: only the cause taken out, the failure gone",
             3: "leave: " + ("a fix at the cause, held by a check that sees the bug" if fix else
                             "the code as it was reproduced")}
    for g in (1, 2, 3):
        print(f"STAGE {g} {names[g]}: " + ("holds" if not problems[g] else f"open, {len(problems[g])} to fix"))
        for line in problems[g]:
            print(f"  - {line}")
    if exps:
        print_table(exps)
    open_stages = [g for g in (1, 2, 3) if problems[g]]
    if open_stages:
        print(f"DEBUG-GATE: open({', '.join(map(str, open_stages))}): fix the lines above, then D --gate")
        return 1
    answer(ledger, cause, proven, fix)
    return 0


def print_table(exps):
    print("\n| # | hypothesis | experiment | result | verdict |\n|---|---|---|---|---|")
    for e in exps:
        last = e["tail"][-1] if e["tail"] else f"exit {e['exit']}"
        print(f"| {e['n']} | {e['why'][:90]} | {e['file']}:{e['start']} `{e['was'].strip()[:40]}` -> "
              f"`{(e['as'].strip() or '<removed>')[:40]}` | {last[:60]} | {e['verdict']} |")


def answer(ledger, cause, proven, fix):
    rp, suite = ledger["repro"], ledger.get("suite") or {}
    print("\nANSWER (drafted from the ledger; give it, adding only context):\n")
    print(f"Failure: `{rp['cmd']}` shows `{rp['wrong']}` where it should show `{rp['right']}` "
          f"(exit {rp['exit']}).")
    func = f" in `{cause['function']}`" if cause.get("function") else ""
    print(f"Cause, proven both ways: {cause['file']}:{cause['start']}{func}, `{cause['was'].strip()}`. "
          f"{cause['why']}")
    print(f"- with it: `{rp['cmd']}` shows `{rp['wrong']}`")
    print(f"- with only that line as `{cause['as'].strip() or '<removed>'}`: it shows `{rp['right']}`")
    if suite.get("cmd"):
        entered = {os.path.normcase(e) for e in suite.get("entered", [])}
        if cause.get("first"):
            what = f"`{cause['function']}`"
            reached = os.path.normcase(f"{cause['file']}:{cause['first']}") in entered
        else:
            what = cause["file"]
            reached = any(e.rsplit(":", 1)[0] == os.path.normcase(cause["file"]) for e in entered)
        state = "passes" if suite.get("exit") == 0 and not suite.get("no_tests") else \
            ("runs no tests" if suite.get("no_tests") else f"fails (exit {suite.get('exit')}: "
                                                            f"{' / '.join(suite.get('tail', [])[-1:])})")
        if state == "passes":
            seen = f"no test enters {what}" if not reached else f"tests enter {what}, but none fails on it"
        else:
            seen = "so the failure was there to see" if reached else f"though no test enters {what}"
        print(f"Why it was not caught: `{suite['cmd']}` {state} on the broken code; {seen}. "
              "[[fill: what the tests feed it, and what they never try]]")
    else:
        print("Why it was not caught: no test suite found. [[fill: what would have caught it]]")
    if fix:
        rr = ledger["regress"]
        print(f"Changed: {', '.join(ledger['_changed'])}. `{rr['cmd']}` fails with the cause put back "
              f"(exit {rr['cause_back']['exit']}: {' / '.join(rr['cause_back']['tail'][-1:])}) and passes now.")
    else:
        print("Nothing changed: the code is as it was reproduced. Regression test to add: "
              "[[fill: the minimal reproduction as a test, and where it goes]]")
    if ledger.get("_added"):
        print("Files added: " + ", ".join(ledger["_added"][:8]))
    print("Not covered: [[fill: what this run could not exercise]]")
    print(f"\nDEBUG-GATE: done({len(proven)} proven of {len(ledger.get('experiments', []))} experiments"
          + (", fixed and held" if fix else ", diagnosis only") + ")")


def overview(repo):
    ledger = read_json(repo, LEDGER, {})
    if not ledger.get("repro"):
        print('Nothing recorded. Start: D --repro "<cmd>" --wrong "<text>" --right "<text>"')
        return 0
    rp = ledger["repro"]
    print(f"Reproduced: `{rp['cmd']}` shows {rp['wrong']!r}, should show {rp['right']!r}")
    if ledger.get("experiments"):
        print_table(ledger["experiments"])
    print("next: D --gate")
    return 0


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description="Reproduce, prove the cause both ways, and leave the tree honest.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--repro", metavar="CMD", help="the command that shows the failure")
    ap.add_argument("--wrong", help="text the failing output shows")
    ap.add_argument("--right", help="text the output should show instead")
    ap.add_argument("--prove", metavar="FILE:LINE[-END]", help="lines holding the suspected cause")
    ap.add_argument("--as", dest="as_text", metavar="TEXT", help="those lines without the cause ('' removes them)")
    ap.add_argument("--why", help="the hypothesis, one sentence that could be wrong")
    ap.add_argument("--tests", help="the test suite command (default: found from the repo)")
    ap.add_argument("--gate", action="store_true", help="check the three stages")
    ap.add_argument("--regress", metavar="CMD", help="with --gate: the regression check for a fix")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per command")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo)
    if a.repro is not None:
        return repro(repo, a.repro, a.wrong, a.right, a.timeout)
    if a.prove is not None:
        return prove(repo, a.prove, a.as_text, a.why, a.tests, a.timeout)
    if a.gate or a.regress:
        return gate(repo, a.regress, a.timeout)
    return overview(repo)


if __name__ == "__main__":
    sys.exit(main())
