#!/usr/bin/env python3
"""threat.py - the mechanical side of the threat-model skill.

A model that reads the code well finds the hole it is pointed at, and usually proves it with a probe
it then deletes. This keeps the two things it skips: the count of every way in (route tables,
registering decorators, handler classes, `__main__` blocks), so the second door to the same data is
on the list, and each attack as a kept test that ran through the door it names.

  T                         the doors found, the attacks recorded, what is open
  T --attack CMD --door FILE::FUNC [--door ...] --gets TEXT
                            run CMD (a test that passes only when the abuse is refused) in a
                            throwaway copy under a call tracer. Recorded `open` when it fails (the
                            abuse works), `held` when it passes. Refused when it never enters a door
                            it names, runs no tests, or errors instead of failing an assertion.
                            The first attack keeps the tree as it was in .threat/before/
  T --gate                  check the stages and print every problem with its fix:
    1 doors    the scan found the ways in (or --door named them)
    2 attack   every door is entered by a recorded attack, or has `- DOOR: out: <why>` in
               .threat/doors.md (the gate appends the slots)
    3 hold     every attack reruns as recorded; after a fix, every attack passes now and every
               attack that was open fails again with the changed files put back

`T` is `python threat.py <repo>`. Stdlib only.
"""
import argparse, ast, hashlib, json, os, re, shlex, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _encoding import utf8_streams  # noqa: E402

STATE = ".threat"
BEFORE = f"{STATE}/before"
LEDGER = f"{STATE}/state.json"
NOTES = f"{STATE}/doors.md"
FILL = "[[fill"
# Folders that hold tools' state or caches, never the product: not scanned, copied or compared.
NOT_PRODUCT = {".git", "__pycache__", "node_modules", ".venv", "venv", STATE, ".debug", ".wire", ".latent",
               ".features", ".structure", ".verify-state-cache", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".evolve"}
NOT_PRODUCT_FILES = {".verify-state.json"}
OTHER_CODE = {".js", ".mjs", ".ts", ".tsx", ".jsx", ".rb", ".go", ".php", ".java", ".kt", ".cs", ".rs"}
BASH = shutil.which("bash")
NO_TESTS = re.compile(r"^Ran 0 tests\b|\bno tests ran\b", re.MULTILINE | re.IGNORECASE)
ERRORED = re.compile(r"^FAILED \((?:failures=\d+, )?errors=\d+|\b\d+ errors?\b(?! in)|^ERROR: ", re.MULTILINE)
# Decorators that wrap a function without exposing it.
NOT_REGISTERING = {"property", "staticmethod", "classmethod", "wraps", "lru_cache", "cache", "cached_property",
                   "dataclass", "contextmanager", "asynccontextmanager", "abstractmethod", "total_ordering",
                   "patch", "fixture", "mark", "parametrize", "skip", "skipIf", "skipUnless", "overload",
                   "setter", "getter", "deleter", "singledispatch", "register_dataclass", "deprecated"}
ROUTE_WORD = re.compile(r"route|^(get|post|put|patch|delete|head|options)$|command|task|handler|receiver|"
                        r"subscri|listen|websocket|api_view|job|^on$|^on_|endpoint|hook|tool", re.IGNORECASE)
REGISTER_CALL = re.compile(r"register|add_route|add_url_rule|add_api_route|route|connect|subscribe|^on$|"
                           r"add_command|add_handler|set_defaults|command|add_job|schedule", re.IGNORECASE)
REGISTER_KW = {"func", "view_func", "handler", "callback", "target", "endpoint", "view", "action"}
# An `out:` reason that leans on a defense: a defense read about is what an attack has to prove.
CLAIMS_DEFENSE = re.compile(r"\b(check|guard|requir|protect|restrict|verif|validat|reject|refus|den(y|ies)|"
                            r"forbid|403|401|auth|staff|admin|owner|secure|sanitiz|escap|bounded|limited)", re.IGNORECASE)

TRACER = r'''import atexit, os, sys, threading
_tm_root = os.path.normcase(os.path.abspath(os.environ.get("THREAT_ROOT", ".")))
_tm_seen = set()
def _tm_profile(frame, event, arg):
    if event == "call":
        _tm_seen.add((frame.f_code.co_filename, frame.f_code.co_firstlineno))
def _tm_dump():
    sys.setprofile(None)
    threading.setprofile(None)
    try:
        with open(os.environ["THREAT_CALL_LOG"], "a", encoding="utf-8") as fh:
            for f, line in list(_tm_seen):
                p = os.path.normcase(os.path.abspath(f))
                if p.startswith(_tm_root + os.sep):
                    fh.write(f"{p}\t{line}\n")
    except Exception:
        pass
sys.setprofile(_tm_profile)
threading.setprofile(_tm_profile)
atexit.register(_tm_dump)
'''


# ---------------- files and runs -------------------------------------------------
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


def copy_tree(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*NOT_PRODUCT, "*.pyc"))


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


def run_copy(src, cmd, timeout, edits=None):
    """Run CMD under the call tracer in a throwaway copy of SRC with EDITS ({rel: source path} or
    {rel: None} to delete) applied first. (exit, output, {(rel file, first line)} entered)."""
    tmp = tempfile.mkdtemp(prefix="threat-")
    try:
        root = os.path.join(tmp, "repo")
        copy_tree(src, root)
        for r, source in (edits or {}).items():
            dest = os.path.join(root, *r.split("/"))
            if source is None:
                if os.path.exists(dest):
                    os.remove(dest)
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(source, dest)
        hook = os.path.join(tmp, "hook")
        os.makedirs(hook)
        with open(os.path.join(hook, "sitecustomize.py"), "w", encoding="utf-8") as fh:
            fh.write(TRACER)
        log = os.path.join(hook, "calls.txt")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", THREAT_ROOT=root, THREAT_CALL_LOG=log)
        env["PYTHONPATH"] = os.pathsep.join([hook, root] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
        # Agents write commands in the shell they use (`VAR=x cmd`, `&&`), so prefer bash.
        argv = [BASH, "-c", cmd] if BASH else cmd
        try:
            p = subprocess.run(argv, cwd=root, shell=not BASH, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout, env=env)
            code, text = p.returncode, (p.stdout or "") + (p.stderr or "")
        except subprocess.TimeoutExpired:
            code, text = "timeout", "timed out"
        entered = set()
        try:
            with open(log, encoding="utf-8") as fh:
                for row in fh:
                    path, _, line = row.rstrip("\n").rpartition("\t")
                    if line.isdigit():
                        entered.add((rel(path, os.path.normcase(os.path.abspath(root))), int(line)))
        except OSError:
            pass
        return code, text.replace(root, "<repo>"), entered
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def tail(text, n=4):
    return [ln[:200] for ln in text.splitlines() if ln.strip()][-n:]


# ---------------- stage 1: doors --------------------------------------------------
def is_test_file(r):
    parts = r.split("/")
    return any(p in ("tests", "test") for p in parts[:-1]) or re.match(r"^(test_.+|.+_test|conftest)\.py$", parts[-1])


def last_name(node):
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def scan_file(path, r):
    """{door id: {file, func, line, why}} for one Python file; None when it does not parse."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            tree = ast.parse(fh.read())
    except (SyntaxError, ValueError):
        return None
    doors, top = {}, {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            top[node.name] = node

    def first_line(fn):
        return min([fn.lineno] + [d.lineno for d in fn.decorator_list])

    def add(fn, qual, why):
        doors.setdefault(f"{r}::{qual}", {"file": r, "func": qual, "line": first_line(fn), "why": why})

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = prefix + child.name
                for dec in child.decorator_list:
                    name = last_name(dec)
                    if name in NOT_REGISTERING:
                        continue
                    if isinstance(dec, ast.Call) or ROUTE_WORD.search(name):
                        add(child, qual, f"decorated @{name}")
                        break
                if prefix and re.match(r"^do_[A-Z]+$", child.name):
                    add(child, qual, "HTTP handler method")
                walk(child, qual + ".")
            elif isinstance(child, ast.ClassDef):
                walk(child, prefix + child.name + ".")
            else:
                walk(child, prefix)
    walk(tree, "")

    # functions listed in a module-level table: ROUTES = {("GET", "x"): handler, ...}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None and \
                isinstance(node.value, (ast.Dict, ast.List, ast.Tuple, ast.Set)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            label = last_name(target) or "a table"
            for sub in ast.walk(node.value):
                if isinstance(sub, ast.Name) and sub.id in top:
                    add(top[sub.id], sub.id, f"listed in {label}")
    # functions handed to a registering call: app.add_url_rule("/x", view_func=f), sub.set_defaults(func=f)
    for sub in ast.walk(tree):
        if not isinstance(sub, ast.Call):
            continue
        called = last_name(sub)
        args = [(None, a) for a in sub.args] + [(k.arg, k.value) for k in sub.keywords]
        for kw, a in args:
            if isinstance(a, ast.Name) and a.id in top and (kw in REGISTER_KW or REGISTER_CALL.search(called)):
                add(top[a.id], a.id, f"registered by {called}()")
    for node in tree.body:
        if isinstance(node, ast.If) and "__name__" in ast.dump(node.test) and "__main__" in ast.dump(node.test):
            doors.setdefault(f"{r}::__main__", {"file": r, "func": "__main__", "line": node.lineno,
                                                 "why": "runs as a script"})
    return doors


def scan(repo):
    """(doors, files no parser here could scan)."""
    doors, unscanned = {}, []
    for p in walk_files(repo):
        r = rel(p, repo)
        ext = os.path.splitext(r)[1].lower()
        if ext == ".py" and not is_test_file(r):
            found = scan_file(p, r)
            if found is None:
                unscanned.append(r)
            else:
                doors.update(found)
        elif ext in OTHER_CODE and not r.startswith(BEFORE):
            unscanned.append(r)
    return doors, unscanned


def all_doors(repo, ledger):
    doors, unscanned = scan(repo)
    for d, info in (ledger.get("named") or {}).items():
        doors.setdefault(d, info)
    for r in unscanned:
        doors.setdefault(r, {"file": r, "func": None, "line": None, "why": "no parser here: name its doors with --door"})
    return doors


def entered_door(door, info, entered, cmd):
    """Did a run enter this door? Functions by the tracer; a script or a file by the command naming it."""
    if info.get("func") and info["func"] != "__main__" and info.get("line"):
        return (os.path.normcase(info["file"]), info["line"]) in {(os.path.normcase(f), ln) for f, ln in entered}
    if info.get("func") == "__main__" or info.get("line") is None:
        name = info["file"]
        return name in cmd or any(os.path.normcase(f) == os.path.normcase(name) for f, _ in entered)
    return False


# ---------------- stage 2: attack -------------------------------------------------
def outside_paths(repo, cmd):
    """Absolute paths in CMD that are not inside the repo: an attack kept there does not rerun."""
    try:
        tokens = shlex.split(cmd, posix=os.name != "nt")
    except ValueError:
        tokens = cmd.split()
    out = []
    for t in tokens:
        t = t.strip("'\"")
        if (t.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", t)) and not t.startswith("-"):
            if not os.path.normcase(os.path.abspath(t)).startswith(os.path.normcase(repo) + os.sep):
                out.append(t)
    return out


def attack_files(repo, cmd):
    """The repo files an attack command names: `tests/test_x.py[::T]`, or a dotted `tests.test_x.T`."""
    try:
        tokens = shlex.split(cmd, posix=os.name != "nt")
    except ValueError:
        tokens = cmd.split()
    found = set()
    for t in tokens:
        t = t.strip("'\"").split("::")[0]
        if t.endswith(".py") and os.path.isfile(os.path.join(repo, t)):
            found.add(rel(os.path.join(repo, t), repo))
        elif re.match(r"^[A-Za-z_]\w*(\.[A-Za-z_]\w*)+$", t):
            parts = t.split(".")
            for n in range(len(parts), 0, -1):
                cand = os.path.join(repo, *parts[:n]) + ".py"
                if os.path.isfile(cand):
                    found.add(rel(cand, repo))
                    break
    return sorted(found)


def suite_runs(r):
    """Would the project's own test run pick this file up (unittest `test*.py`, pytest `*_test.py`)?"""
    name = r.rsplit("/", 1)[-1]
    return not r.startswith(STATE + "/") and bool(re.match(r"^test.*\.py$|^.+_test\.py$", name))


def classify(code, out):
    if code == "timeout":
        return "error", "timed out"
    if NO_TESTS.search(out):
        return "error", "ran no tests"
    if code == 0:
        return "held", ""
    if ERRORED.search(out):
        return "error", "errored instead of failing an assertion"
    return "open", ""


def attack(repo, cmd, doors_named, gets, timeout):
    if not (cmd and doors_named and (gets or "").strip()):
        print('ATTACK: give all three: T --attack "<test cmd that passes only if the abuse is refused>" '
              '--door FILE::FUNC --gets "<what the attacker gets if it works>"')
        return 2
    outside = outside_paths(repo, cmd)
    if outside:
        print(f"ATTACK: {', '.join(outside)} is outside the repo. Keep the attack in the repo (tests/ is "
              "fine) so it reruns after a fix and stays as the regression check.")
        return 2
    files = attack_files(repo, cmd)
    if not files:
        print("ATTACK: the command names no test file in the repo. Name the attack's own file "
              "(`python -m unittest tests.test_attacks.Export`, `python -m pytest tests/test_attacks.py::test_x`): "
              "a whole-suite run enters every door through the honest tests and proves nothing about abuse.")
        return 2
    hidden = [f for f in files if not suite_runs(f)]
    if hidden:
        print(f"ATTACK: {', '.join(hidden)} is not a file the project's test run picks up. Keep attacks in "
              "tests/test_*.py so every later run of the suite repeats them.")
        return 2
    ledger = read_json(repo, LEDGER, {})
    doors = all_doors(repo, ledger)
    for d in doors_named:
        if d not in doors:
            m = re.match(r"^(.+?)::(.+)$", d)
            if not m or not os.path.isfile(os.path.join(repo, *m.group(1).split("/"))):
                print(f"ATTACK: {d} is not a door the scan found and not FILE::FUNC of a file here. "
                      f"Doors found: {', '.join(sorted(doors)[:12])}")
                return 2
            found = scan_file(os.path.join(repo, *m.group(1).split("/")), m.group(1)) or {}
            info = found.get(d) or function_door(repo, m.group(1), m.group(2))
            if not info:
                print(f"ATTACK: no function {m.group(2)} in {m.group(1)}.")
                return 2
            info["why"] = "named by --door"
            ledger.setdefault("named", {})[d] = info
            doors[d] = info
    before = os.path.join(repo, BEFORE)
    if not os.path.isdir(before):
        copy_tree(repo, before)   # the tree as it was when the first attack ran, kept for the hold stage
    code, out, entered = run_copy(repo, cmd, timeout)
    reached = [d for d in doors_named if entered_door(d, doors[d], entered, cmd)]
    missed = [d for d in doors_named if d not in reached]
    status, why = classify(code, out)
    print(f"ATTACK: exit {code}  {cmd}")
    print("".join(f"  | {ln}\n" for ln in tail(out, 5)), end="")
    if missed:
        print(f"ATTACK: never entered {', '.join(missed)}: the run proves nothing about "
              f"{'it' if len(missed) == 1 else 'them'}. Call through the door, or name the door it does reach.")
    if not reached:
        save(repo, ledger)
        return 1
    if status == "error":
        print(f"ATTACK: not recorded: {why}. An attack must pass when the abuse is refused and fail an "
              "assertion when it works; a crash says neither.")
        save(repo, ledger)
        return 1
    attacks = [a for a in ledger.get("attacks", []) if a["cmd"] != cmd]
    entry = {"n": max([a["n"] for a in ledger.get("attacks", [])] + [0]) + 1, "cmd": cmd, "doors": reached,
             "files": files,
             "gets": gets.strip(), "status": status, "exit": code, "tail": tail(out, 3)}
    ledger["attacks"] = attacks + [entry]
    save(repo, ledger)
    word = "OPEN: the abuse works" if status == "open" else "HELD: the abuse is refused"
    print(f"ATTACK {entry['n']}: {word} through {', '.join(reached)}")
    print("next: attack or account for the other doors, then T --gate")
    return 0


def function_door(repo, f, qual):
    try:
        with open(os.path.join(repo, *f.split("/")), encoding="utf-8", errors="replace") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError, ValueError):
        return None
    node, parts = tree, qual.split(".")
    for part in parts:
        node = next((c for c in ast.iter_child_nodes(node) if isinstance(
            c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and c.name == part), None)
        if node is None:
            return None
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return None
    return {"file": f, "func": qual, "line": min([node.lineno] + [d.lineno for d in node.decorator_list])}


# ---------------- notes -----------------------------------------------------------
def read_notes(repo):
    """{door: reason} for `- DOOR: out: <why>` lines; filled slots only."""
    out, text = {}, ""
    try:
        with open(os.path.join(repo, NOTES), encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return out, text
    for line in text.splitlines():
        m = re.match(r"^\s*-\s*`?([^`\s]+?)`?\s*[:|]\s*out\s*:\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
        else:
            m = re.match(r"^\s*-\s*`?([^`\s]+?)`?\s*[:|]\s*(\[\[fill.*)$", line)
            if m:
                out.setdefault(m.group(1), m.group(2).strip())
    return out, text


def append_slots(repo, doors, notes, text):
    lines = [f"- {d}: {FILL}: out: <why an attacker gains nothing through it>, or attack it with T --attack]]"
             for d in doors if d not in notes]
    if not lines:
        return 0
    head = "" if text else ("# Doors\n\nOne line per way in that no attack entered: `- DOOR: out: <why>`. "
                            "A door an attack entered needs no line.\n\n")
    sep = "" if not text or text.endswith("\n") else "\n"
    path = os.path.join(repo, NOTES)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(head + sep + "\n".join(lines) + "\n")
    return len(lines)


# ---------------- stage 3: hold, and the gate ------------------------------------
def gate(repo, timeout):
    ledger = read_json(repo, LEDGER, {})
    problems = {1: [], 2: [], 3: []}
    print('T = python "' + os.path.abspath(__file__) + '" ' + repo)
    doors = all_doors(repo, ledger)
    if not doors:
        problems[1].append("the scan found no way in (no route table, registering decorator, handler class or "
                           "__main__ block). Name each one: T --attack \"<cmd>\" --door FILE::FUNC --gets \"...\"")
    attacks = ledger.get("attacks", [])
    attacked = {d for a in attacks for d in a["doors"]}
    notes, text = read_notes(repo)
    if doors:
        if not attacks:
            problems[2].append('no attack recorded. Write a test that passes only when the abuse is refused, then '
                               'T --attack "<test cmd>" --door FILE::FUNC --gets "<what the attacker gets>"')
        unaccounted = [d for d in sorted(doors) if d not in attacked]
        added = append_slots(repo, unaccounted, notes, text)
        if added:
            notes, text = read_notes(repo)
            print(f"(appended {added} slot{'s' if added != 1 else ''} to {NOTES})")
        for d in unaccounted:
            reason = notes.get(d, "")
            if not reason or reason.startswith(FILL):
                problems[2].append(f"{d} ({doors[d]['why']}): no attack entered it and {NOTES} gives no reason. "
                                   "Attack it, or fill its line with `out: <why an attacker gains nothing>`")
            elif len(reason.split()) < 4:
                problems[2].append(f"{d}: `out: {reason}` says too little. Say why an attacker gains nothing "
                                   "through it (public by design, no input, no state), or attack it")
            elif CLAIMS_DEFENSE.search(reason):
                problems[2].append(f"{d}: `out: {reason[:70]}` leans on a defense. A defense you read about is "
                                   "what an attack has to prove: attack it. `out:` is for a door with nothing "
                                   "behind it (public by design, no input, no state)")
        for d in sorted(notes):
            if d not in doors:
                problems[2].append(f"{NOTES} has a line for {d}, which is not a door now. Delete the line")

    before = os.path.join(repo, BEFORE)
    fixed, changed = False, []
    if attacks and os.path.isdir(before):
        was, now = product_files(before), product_files(repo)
        oracle = {f for a in attacks for f in a.get("files", [])}   # the attacks judge the change, never part of it
        changed = sorted(f for f in was if now.get(f) != was[f] and f not in oracle)
        fixed = bool(changed)
        put_back = {f: os.path.join(before, *f.split("/")) for f in changed}
        for a in attacks:
            code, out, entered = run_copy(repo, a["cmd"], timeout)
            status, why = classify(code, out)
            a["now"] = status
            if status == "error":
                problems[3].append(f"attack {a['n']} `{a['cmd']}` {why} on the tree now ({' / '.join(tail(out, 1))})")
            elif fixed and status != "held":
                problems[3].append(f"attack {a['n']} is still open after the change ({a['gets']}). Fix every door "
                                   f"it enters: {', '.join(a['doors'])}")
            elif not fixed and status != a["status"]:
                problems[3].append(f"attack {a['n']} was {a['status']} when recorded and is {status} now, with no "
                                   "product file changed. Make it deterministic, then record it again")
            if fixed and a["status"] == "open":
                bcode, bout, _ = run_copy(repo, a["cmd"], timeout, edits=put_back)
                bstatus, _ = classify(bcode, bout)
                a["back"] = bstatus
                if bstatus != "open":
                    problems[3].append(f"attack {a['n']} does not fail with {', '.join(changed)} put back as it was "
                                       f"({bstatus}): it cannot see the abuse it was recorded on")
        save(repo, ledger)
    elif attacks:
        problems[3].append(f"{BEFORE}/ is missing: record the attacks again so the tree as it was is kept")

    names = {1: "doors: every way in found", 2: "attack: every door attacked or accounted for",
             3: "hold: " + ("the change shuts every open attack, and each one fails with it taken out" if fixed
                            else "every attack reruns as recorded")}
    for g in (1, 2, 3):
        print(f"STAGE {g} {names[g]}: " + ("holds" if not problems[g] else f"open, {len(problems[g])} to fix"))
        for line in problems[g]:
            print(f"  - {line}")
    open_stages = [g for g in (1, 2, 3) if problems[g]]
    if open_stages:
        print(f"THREAT-GATE: open({', '.join(map(str, open_stages))}): fix the lines above, then T --gate")
        return 1
    answer(ledger, doors, notes, fixed, changed)
    return 0


def answer(ledger, doors, notes, fixed, changed):
    attacks = ledger["attacks"]
    attacked = {d for a in attacks for d in a["doors"]}
    out_doors = sorted(d for d in doors if d not in attacked)
    was_open = [a for a in attacks if a["status"] == "open"]
    print("\nANSWER (drafted from the recorded attacks; give it, adding only context):\n")
    if fixed:
        print(f"Was open, now shut ({len(was_open)}): each attack below failed on the code as it was, passes now, "
              f"and fails again with {', '.join(changed)} put back.")
    elif was_open:
        print(f"Open today ({len(was_open)}), worst first: [[fill: order these by what the attacker gets]]")
    else:
        print("No recorded attack works today. That is what was tried, not a claim that it is secure.")
    for a in was_open:
        print(f"- {a['gets']}: through {', '.join(a['doors'])}; `{a['cmd']}`"
              + ("" if fixed else ". Fix: [[fill: the contained fix, where the decision really belongs]]"))
    held = [a for a in attacks if a["status"] == "held"]
    if held:
        print(f"Held ({len(held)}): " + "; ".join(f"{a['gets']} ({', '.join(a['doors'])})" for a in held))
    print(f"Doors: {len(doors)} found, {len(attacked)} attacked, {len(out_doors)} with no attack (out:)"
          + (": " + "; ".join(f"{d} ({notes.get(d, '')[:60]})" for d in out_doors[:8]) if out_doors else "") + ".")
    kept = sorted({f for a in attacks for f in a.get("files", [])})
    print(f"Attacks kept where the suite runs them: {', '.join(kept)}. A later change that reopens a door fails them.")
    print("Not covered: [[fill: assets and boundaries no attack here reached (config, secrets, dependencies, "
          "concurrency), and what was only read]]")
    print(f"\nTHREAT-GATE: done({len(was_open)} {'shut' if fixed else 'open'}, {len(held)} held, "
          f"{len(attacked)}/{len(doors)} doors attacked)")


def overview(repo):
    ledger = read_json(repo, LEDGER, {})
    doors, unscanned = scan(repo)
    print(f"{len(doors)} doors found" + (f"; no parser here for {len(unscanned)} files: {', '.join(unscanned[:6])}"
                                         if unscanned else "") + ":")
    for d, info in sorted(doors.items()):
        print(f"  {d}  ({info['why']})")
    for a in ledger.get("attacks", []):
        print(f"attack {a['n']} {a['status']}: {a['gets']} via {', '.join(a['doors'])}  `{a['cmd']}`")
    print('next: T --attack "<test cmd>" --door FILE::FUNC --gets "<what the attacker gets>", then T --gate')
    return 0


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description="Every way in, each attack kept as a test, each fix held.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--attack", metavar="CMD", help="a test command that passes only when the abuse is refused")
    ap.add_argument("--door", action="append", metavar="FILE::FUNC", help="the way in the attack goes through")
    ap.add_argument("--gets", help="what the attacker gets if it works")
    ap.add_argument("--gate", action="store_true", help="check the three stages")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per command")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo)
    if a.attack is not None:
        return attack(repo, a.attack, a.door or [], a.gets, a.timeout)
    if a.gate:
        return gate(repo, a.timeout)
    return overview(repo)


if __name__ == "__main__":
    sys.exit(main())
