#!/usr/bin/env python3
"""wire.py - the mechanical side of the wire-check skill.

Reading code says what *could* reach a function. This records what *did*: every command you name
runs in a throwaway copy of the repo with a call tracer (a `sitecustomize` that profiles every
Python process the command starts), and the functions it entered are written down. The rest is
bookkeeping a model skips when it is in a hurry:

  W                        the ways in this repo declares, and how many functions it defines
  W --snapshot --run CMD   run each CMD in a copy under the tracer; .wire/snapshot.json
                           (a snapshot taken after the code changed keeps the first as before.json)
  W --gate [--run CMD ...] [--target FILE::FUNC ...]
                           check the stages and print every problem with its fix:
    1 snapshot  current, and every declared way in was started (or `- entry X: not run: why`)
    2 account   every function no command entered has a verdict in .wire/verdicts.md
    3 keep      (only with targets: components you connected) each target is entered by a real
                command now, has a FEATURES.md trace (feature-map) and a VERIFY.md check seen
                rejecting the broken wiring (verify-loop)

`W` is `python wire.py <repo>`. Stdlib only.
"""
import argparse, ast, hashlib, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _encoding import utf8_streams  # noqa: E402

SIBLING = os.path.join(os.path.dirname(os.path.dirname(HERE)), "{0}", "scripts", "{1}")
STATE = ".wire"
SNAPSHOT = f"{STATE}/snapshot.json"
BEFORE = f"{STATE}/before.json"
TARGETS = f"{STATE}/targets.json"
VERDICTS = f"{STATE}/verdicts.md"
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "env", "build", "dist",
             STATE, ".features", ".verify-state", ".pytest_cache", ".mypy_cache", ".blast"}
COPY_IGNORE = shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".venv", "venv", "*.pyc", STATE)
BASH = shutil.which("bash")
CLASSES = ("served", "not-registered", "not-routed", "never-invoked", "effect-lost", "unknown")
CITED = {"served", "not-routed", "never-invoked", "effect-lost"}
VERDICTS_HEAD = """# Wire verdicts

One line per function (or whole file) no snapshot command entered:
`- <file>[::<function>]: <class>: <why>`. Classes: served (reached by a way in that cannot run
here; cite the file:line that reaches it), not-registered (nothing names it), not-routed (registered,
but no trigger maps to it; cite where it should be), never-invoked (a flag or branch nobody takes;
cite it), effect-lost (it runs, or should, but its result is dropped; cite the line), unknown
(depends on something outside the repo; say what). A declared way in you could not start:
`- entry <name>: not run: <why>`.

"""

TRACER = r'''import atexit, os, sys, threading
_wire_root = os.path.normcase(os.path.abspath(os.environ.get("WIRE_ROOT", ".")))
_wire_seen = set()
def _wire_profile(frame, event, arg):
    if event == "call":
        code = frame.f_code
        key = (code.co_filename, code.co_firstlineno)
        if key not in _wire_seen:
            _wire_seen.add(key)
def _wire_dump():
    sys.setprofile(None)
    threading.setprofile(None)
    try:
        with open(os.environ["WIRE_CALL_LOG"], "a", encoding="utf-8") as fh:
            for f, line in list(_wire_seen):
                p = os.path.normcase(os.path.abspath(f))
                if p.startswith(_wire_root + os.sep):
                    fh.write(f"{p}\t{line}\n")
    except Exception:
        pass
sys.setprofile(_wire_profile)
threading.setprofile(_wire_profile)
atexit.register(_wire_dump)
'''


# ---------------- what the repo declares --------------------------------------
def rel(path, repo):
    return os.path.relpath(path, repo).replace(os.sep, "/")


def is_test(rel_path):
    parts = rel_path.split("/")
    name = parts[-1]
    return (any(p in ("tests", "test", "testing") for p in parts[:-1]) or name.startswith("test_")
            or name.endswith("_test.py") or name == "conftest.py")


def check_files(repo):
    """Python files VERIFY.md names (its checks and oracles): instruments, not product."""
    lines = [m.group(2) for m in re.finditer(r"(?m)^\s*-\s*([\w-]+):(.*)$", read_text(repo, "VERIFY.md"))
             if m.group(1) not in ("path", "fail-proof", "fail-signal", "features", "fresh")]
    return {p.replace("\\", "/").lstrip("./") for ln in lines for p in re.findall(r"[\w./\\-]+\.py", ln)}


def py_files(repo):
    out, checks = [], check_files(repo)
    for d, subdirs, names in os.walk(repo):
        subdirs[:] = sorted(s for s in subdirs if s not in SKIP_DIRS and not s.startswith(".verify"))
        for n in sorted(names):
            if n.endswith(".py"):
                r = rel(os.path.join(d, n), repo)
                if not is_test(r) and r != "setup.py" and r not in checks:
                    out.append(r)
    return out


def parse(repo, rel_path):
    try:
        with open(os.path.join(repo, rel_path), encoding="utf-8", errors="replace") as fh:
            return ast.parse(fh.read())
    except (SyntaxError, ValueError, OSError):
        return None


def first_line(node):
    """The line a running function reports as co_firstlineno: its first decorator, else `def`."""
    return min([node.lineno] + [d.lineno for d in node.decorator_list])


def inventory(repo):
    """{"file::qualname": [file, first line]} for every top-level function and every method of a
    top-level class (dunders other than __init__/__call__ left out), plus files that would not parse."""
    funcs, broken = {}, []
    for f in py_files(repo):
        tree = parse(repo, f)
        if tree is None:
            broken.append(f)
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs[f"{f}::{node.name}"] = [f, first_line(node)]
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not (
                            item.name.startswith("__") and item.name not in ("__init__", "__call__")):
                        funcs[f"{f}::{node.name}.{item.name}"] = [f, first_line(item)]
    return funcs, broken


def read_text(repo, rel_path):
    try:
        with open(os.path.join(repo, rel_path), encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def declared_entries(repo):
    """[(name, kind, file, function or None)]: every way in the repo declares in a form a script
    can read. Console scripts (pyproject.toml, setup.cfg), `python -m` packages, and files with a
    top-level `if __name__ == "__main__"`."""
    out = []
    for cfg in ("pyproject.toml", "setup.cfg"):
        text = read_text(repo, cfg)
        section = None
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("["):
                section = s.strip("[]").strip()
                continue
            in_scripts = section in ("project.scripts", "tool.poetry.scripts", "options.entry_points") \
                or (section or "").endswith("console_scripts")
            m = re.match(r'^"?([\w.-]+)"?\s*=\s*"?([\w.]+):([\w.]+)"?\s*$', s)
            if in_scripts and m:
                mod = m.group(2).replace(".", "/")
                for cand in (f"{mod}.py", f"{mod}/__init__.py"):
                    if os.path.isfile(os.path.join(repo, cand)):
                        out.append((m.group(1), "console script", cand, m.group(3)))
                        break
    for f in py_files(repo):
        if f.endswith("/__main__.py"):
            out.append((f"python -m {f[:-len('/__main__.py')].replace('/', '.')}", "-m package", f, None))
            continue
        tree = parse(repo, f)
        for node in (tree.body if tree else []):
            if isinstance(node, ast.If) and "__name__" in ast.dump(node.test) and "__main__" in ast.dump(node.test):
                out.append((f, "__main__ script", f, None))
                break
    return out


LOADER = re.compile(r"(import_module|__import__|getattr)\s*\((?P<arg>[^)\n]*)")


def runtime_loaders(repo):
    """['file:line  code'] for each place that picks code by a name built at runtime: the links a
    reading cannot follow and a snapshot can, if a command takes that path."""
    out = []
    for f in py_files(repo):
        for i, line in enumerate(read_text(repo, f).splitlines(), 1):
            m = LOADER.search(line)
            if m and ("f\"" in m.group("arg") or "f'" in m.group("arg") or "+" in m.group("arg")
                      or (m.group(1) != "getattr" and not re.match(r"\s*['\"]", m.group("arg")))):
                out.append(f"{f}:{i}  {line.strip()[:100]}")
    return out


# ---------------- the snapshot ------------------------------------------------
def file_sha(repo, rel_path):
    try:
        with open(os.path.join(repo, rel_path), "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()[:16]
    except OSError:
        return None


def read_json(repo, rel_path, default=None):
    try:
        with open(os.path.join(repo, rel_path), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_json(repo, rel_path, data):
    path = os.path.join(repo, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)


def run_traced(repo, commands, timeout):
    """{cmd: {"exit", "tail", "entered": [file::func ...], "loaded": [file ...]}} for each command,
    run in its own throwaway copy of the repo so the person's data is never touched."""
    funcs, _broken = inventory(repo)
    by_line = {(f, line): key for key, (f, line) in funcs.items()}
    results = {}
    for cmd in commands:
        tmp = tempfile.mkdtemp(prefix="wire-")
        copy = os.path.join(tmp, "repo")
        try:
            shutil.copytree(repo, copy, ignore=COPY_IGNORE)
            hook = os.path.join(tmp, "hook")
            os.makedirs(hook)
            with open(os.path.join(hook, "sitecustomize.py"), "w", encoding="utf-8") as fh:
                fh.write(TRACER)
            log = os.path.join(tmp, "calls.txt")
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", WIRE_ROOT=copy, WIRE_CALL_LOG=log,
                       PYTHONPATH=os.pathsep.join([hook, copy] + ([os.environ["PYTHONPATH"]]
                                                                 if os.environ.get("PYTHONPATH") else [])))
            # The agent writes commands in the shell it uses (`VAR=x cmd`, `&&`), so prefer bash.
            argv = [BASH, "-c", cmd] if BASH else cmd
            try:
                p = subprocess.run(argv, cwd=copy, shell=not BASH, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=timeout, env=env)
                code, text = p.returncode, ((p.stdout or "") + (p.stderr or ""))
            except subprocess.TimeoutExpired:
                code, text = "timeout", "timed out"
            text = text.replace(copy, "<repo>")
            entered, loaded = set(), set()
            root = os.path.normcase(os.path.abspath(copy))
            try:
                with open(log, encoding="utf-8") as fh:
                    for row in fh:
                        path, _, line = row.rstrip("\n").rpartition("\t")
                        r = os.path.relpath(path, root).replace(os.sep, "/")
                        loaded.add(r)
                        key = by_line.get((r, int(line))) if line.isdigit() else None
                        if key:
                            entered.add(key)
            except OSError:
                pass
            results[cmd] = {"exit": code, "tail": [ln for ln in text.splitlines() if ln.strip()][-3:],
                            "entered": sorted(entered), "loaded": sorted(loaded)}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return results


def take_snapshot(repo, commands, timeout=300):
    if not commands:
        print('SNAPSHOT: name the commands to run: W --snapshot --run "<cmd>" --run "<cmd>" ...')
        return 2
    old = read_json(repo, SNAPSHOT)
    shas = {f: file_sha(repo, f) for f in py_files(repo)}
    if old and old.get("shas") != shas and not os.path.isfile(os.path.join(repo, BEFORE)):
        write_json(repo, BEFORE, old)   # the first picture of the code as it was, kept for good
    results = run_traced(repo, commands, timeout)
    write_json(repo, SNAPSHOT, {"commands": commands, "results": results, "shas": shas})
    funcs, _ = inventory(repo)
    entered = {k for r in results.values() for k in r["entered"]}
    print(f"SNAPSHOT: {len(commands)} command(s) entered {len(entered)} of {len(funcs)} functions.")
    for cmd, r in results.items():
        print(f"  exit {r['exit']}  {cmd}  ({len(r['entered'])} functions)"
              + (f"  last: {r['tail'][-1][:120]}" if r["exit"] not in (0, "0") and r["tail"] else ""))
    print("next: W --gate")
    return 0


# ---------------- verdicts ----------------------------------------------------
VERDICT_LINE = re.compile(r"^- (?P<who>[^:\s][^\n]*?(?:::[\w.]+)?): (?P<cls>[\w-]+|\[\[fill[^\]]*\]\]):\s*(?P<why>.*)$")
ENTRY_LINE = re.compile(r"^- entry (?P<name>.+?): not run: (?P<why>.+)$")
CITE = re.compile(r"([\w./\\-]+\.[\w]+):(\d+)")


def read_verdicts(repo):
    """({who: (class, why)}, {entry name: why}, [unfilled who])."""
    verdicts, entries, unfilled = {}, {}, []
    for line in read_text(repo, VERDICTS).splitlines():
        m = ENTRY_LINE.match(line.strip())
        if m:
            entries[m.group("name").strip()] = m.group("why").strip()
            continue
        m = VERDICT_LINE.match(line.strip())
        if not m:
            continue
        who = m.group("who").strip().strip("`")
        if "[[fill" in line:
            unfilled.append(who)
            continue
        verdicts[who] = (m.group("cls"), m.group("why").strip())
    return verdicts, entries, unfilled


def citation_problem(repo, cls, why):
    if cls not in CLASSES:
        return f"class `{cls}` is not one of {', '.join(CLASSES)}"
    if not why or len(why) < 8:
        return "says no why"
    if cls in CITED:
        cites = CITE.findall(why)
        if not cites:
            return f"`{cls}` needs the file:line it rests on"
        for path, line in cites:
            text = read_text(repo, path.replace("\\", "/"))
            if not text:
                return f"cites {path}, which is not in the repo"
            if int(line) < 1 or int(line) > len(text.splitlines()):
                return f"cites {path}:{line}, past the end of the file"
    return None


# ---------------- what keeps a repair -----------------------------------------
def verify_sections(repo):
    """{feature name: [path entries]} from VERIFY.md."""
    out, name = {}, None
    for line in read_text(repo, "VERIFY.md").splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            name = m.group(1)
            out[name] = []
            continue
        m = re.match(r"^\s*-\s*path:\s*(.+)$", line)
        if m and name:
            out[name] += [p.strip().strip("`").rstrip("/") for p in m.group(1).split(",") if p.strip()]
    return out


def feature_traces(repo):
    """{feature: (trace text, status)} from FEATURES.md and any features/*.md it includes."""
    texts = [read_text(repo, "FEATURES.md")]
    for inc in re.findall(r"include:\s*([\w./-]+\.md)", texts[0]):
        texts.append(read_text(repo, inc))
    out = {}
    for text in texts:
        for block in re.split(r"(?m)^##\s+", text)[1:]:
            name = block.splitlines()[0].strip()
            trace = " ".join(re.findall(r"(?m)^\s*-\s*trace:\s*(.+)$", block))
            status = " ".join(re.findall(r"(?m)^\s*-\s*status:\s*(.+)$", block))
            out[name] = (trace, status)
    return out


def keep_problems(repo, target, snap, before):
    """What stage 3 still needs for one connected component, each with its fix."""
    problems = []
    f, _, func = target.partition("::")
    short = func.split(".")[-1]
    reached = [c for c, r in snap["results"].items() if target in r["entered"]] if snap else []
    if not reached:
        problems.append(f"{target}: no snapshot command entered it. Run the real trigger (the CLI command, "
                        f"request or job that should reach it) in W --snapshot")
    # feature-map: a feature whose trace walks to the target, kept current by its own check
    fm = SIBLING.format("feature-map", "features.py")
    if os.path.isfile(fm):
        # A step landing in the target's file is enough: a handler found by an event name or a
        # registry key is never called by name, so the name it is found by is the honest last step.
        hits = [n for n, (trace, status) in feature_traces(repo).items()
                if re.search(rf"`[^`]+`\s*@\s*{re.escape(f)}(?=\s|$|>)", trace)]
        if not hits:
            problems.append(f"{target}: no FEATURES.md feature traces to it. Add the feature with a trace "
                            f"ending `> `{short}` @ {f}` (or, where it is found by a name such as an event "
                            f"or registry key, `> `<that name>` @ {f}`) and prove its entry point "
                            f"(python \"{fm}\" prove --repo . --feature \"<name>\" --copy -- <the trigger>)")
        elif not any("proven" in feature_traces(repo)[n][1] for n in hits):
            problems.append(f"{target}: feature {hits[0]!r} traces to it but is not `proven`. Prove its "
                            f"entry point with features.py prove, then label it proven")
        else:
            p = subprocess.run([sys.executable, fm, "check", repo, "--rerun"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            if p.returncode != 0:
                last = [ln for ln in (p.stdout + p.stderr).splitlines() if ln.strip()][-1:]
                problems.append(f"feature-map check fails: {last[0][:160] if last else p.returncode}. Fix the map")
    # verify-loop: a check over the target's file, seen red on the broken wiring, green now
    vl = SIBLING.format("verify-loop", "verify.py")
    if os.path.isfile(vl):
        covering = [n for n, paths in verify_sections(repo).items()
                    if any(f == p or f.startswith(p + "/") for p in paths)]
        if not covering:
            problems.append(f"{target}: no VERIFY.md section has {f} in its `path:`. Add one whose check fires "
                            f"the real trigger and looks for the effect, with a `fail-signal:` naming the "
                            f"missing effect; then python \"{vl}\" advance . until it records the rejection")
        else:
            p = subprocess.run([sys.executable, vl, "report", repo, "--json"], capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
            try:
                a = json.loads(p.stdout[p.stdout.index("{"):])
            except ValueError:
                a = {}
            rejected = {r["feature"] for r in a.get("rejections", [])}
            failing = {k.split("|", 1)[0] for k in (a.get("gaps") or {}).get("failing", [])}
            ok = [n for n in covering if n in rejected and n not in failing]
            if not ok:
                problems.append(f"{target}: VERIFY.md section {covering[0]!r} has no rejection receipt, or "
                                f"fails now (verdict {a.get('verdict', 'unknown')}). Break the wiring in the "
                                f"product (the link you repaired), run python \"{vl}\" run . to see the "
                                f"fail-signal, restore it, and run again; add a `fail-proof:` line")
            elif a.get("verdict") == "stale":
                problems.append(f"files changed since the last verify.py run: python \"{vl}\" run .")
    return problems, reached


# ---------------- the gate ----------------------------------------------------
def gate(repo, runs=(), targets=(), timeout=300):
    if runs:
        take_snapshot(repo, list(runs), timeout)
        print()
    if targets:
        write_json(repo, TARGETS, sorted(set(targets) | set(read_json(repo, TARGETS, []))))
    targets = read_json(repo, TARGETS, [])
    funcs, broken = inventory(repo)
    snap = read_json(repo, SNAPSHOT)
    before = read_json(repo, BEFORE)
    verdicts, entry_notes, unfilled = read_verdicts(repo)
    problems = {1: [], 2: [], 3: []}
    print('W = python "' + os.path.abspath(__file__) + '" ' + repo)
    entries = declared_entries(repo)

    # stage 1: a current snapshot that started every declared way in
    if snap is None:
        problems[1].append('no snapshot. Run every way in, each command that should reach code, in one call: '
                           'W --snapshot --run "<cmd>" --run "<cmd>" ... (every CLI subcommand, the job '
                           'runner, each by-name variant). Commands run in a throwaway copy')
        entered = set()
        loaded = set()
    else:
        shas = {f: file_sha(repo, f) for f in py_files(repo)}
        changed = sorted(f for f in set(shas) | set(snap["shas"]) if shas.get(f) != snap["shas"].get(f))
        if changed:
            problems[1].append(f"code changed since the snapshot ({', '.join(changed[:4])}"
                               f"{' ...' if len(changed) > 4 else ''}). Take it again: W --snapshot --run ... "
                               "(the first one is kept as the before picture)")
        entered = {k for r in snap["results"].values() for k in r["entered"]}
        loaded = {f for r in snap["results"].values() for f in r["loaded"]}
        for name, kind, f, func in entries:
            started = (f"{f}::{func}" in entered) if func else (f in loaded)
            if not started and name not in entry_notes and f not in entry_notes:
                problems[1].append(f"{kind} `{name}` ({f}) was never started. Add a command that runs it, or "
                                   f"`- entry {name}: not run: <why>` to {VERDICTS}")
    for f in broken:
        problems[1].append(f"{f} does not parse, so nothing in it can be wired: fix it or report it (link 1)")

    # stage 2: every function no command entered is accounted for
    missing, by_file = [], {}
    for key in funcs:
        if key not in entered:
            by_file.setdefault(funcs[key][0], []).append(key)
    for f, keys in sorted(by_file.items()):
        whole = len(keys) == sum(1 for k in funcs if funcs[k][0] == f)
        if whole and f in verdicts:
            covered = keys
            bad = citation_problem(repo, *verdicts[f])
            if bad:
                problems[2].append(f"{f}: {bad}")
        else:
            covered = []
            for k in keys:
                v = verdicts.get(k) or (verdicts.get(f) if f in verdicts else None)
                if v is None:
                    continue
                covered.append(k)
                bad = citation_problem(repo, *v)
                if bad:
                    problems[2].append(f"{k}: {bad}")
        missing += [(f, whole, [k for k in keys if k not in covered])] if len(covered) < len(keys) else []
    if snap is not None and missing and not problems[1]:
        lines = read_text(repo, VERDICTS).splitlines() or VERDICTS_HEAD.rstrip("\n").splitlines() + [""]
        new = []
        for f, whole, keys in missing:
            for who in ([f] if whole else keys):
                if who not in unfilled:
                    new.append(f"- {who}: [[fill: {' | '.join(CLASSES)}]]: [[fill: why, with the file:line]]")
        if new:
            os.makedirs(os.path.join(repo, STATE), exist_ok=True)
            with open(os.path.join(repo, VERDICTS), "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(lines + new) + "\n")
        n = sum(len(k) for _f, _w, k in missing)
        names = [f if whole else k for f, whole, keys in missing for k in (keys[:1] if whole else keys)]
        problems[2].append(f"{n} function(s) no command entered have no verdict; their slots are in {VERDICTS}. "
                           "A function a command should reach: add that command to the snapshot instead. "
                           "Unfilled: " + ", ".join(names[:8]) + (" ..." if len(names) > 8 else ""))

    # stage 3: each component connected in this task stays connected
    reached = {}
    for t in targets:
        if t not in funcs:
            problems[3].append(f"target {t} is not a function this repo defines (file::function or file::Class.method)")
            continue
        p, reached[t] = keep_problems(repo, t, snap, before)
        problems[3] += p

    names = {1: "snapshot: current, every way in started", 2: "account: every unentered function has a verdict",
             3: "keep: each connected component reached, mapped and checked"}
    for g in (1, 2, 3):
        if g == 3 and not targets:
            print("STAGE 3 keep: no targets (only for components you connected: --target FILE::FUNC)")
            continue
        print(f"STAGE {g} {names[g]}: " + ("holds" if not problems[g] else f"open, {len(problems[g])} to fix"))
        for line in problems[g]:
            print(f"  - {line}")
    open_stages = [g for g in (1, 2, 3) if problems[g]]
    if open_stages:
        print(f"WIRE-GATE: open({', '.join(map(str, open_stages))}): fix the lines above, then W --gate")
        return 1

    print("ANSWER (drafted from the ledger; give it, adding only context):\n")
    print(f"Ways in, run here ({len(snap['commands'])}):")
    for cmd in snap["commands"]:
        r = snap["results"][cmd]
        print(f"- `{cmd}`: exit {r['exit']}, entered {len(r['entered'])} functions")
    for name, why in entry_notes.items():
        print(f"- not run: {name}: {why}")
    print(f"\n{len(entered & set(funcs))} of {len(funcs)} functions entered.")
    groups = {}
    unentered = {k for k in funcs if k not in entered} | {funcs[k][0] for k in funcs if k not in entered}
    for who, (cls, why) in verdicts.items():
        if who in unentered:   # a verdict for code a later snapshot did enter is history, not answer
            groups.setdefault(cls, []).append((who, why))
    for cls in CLASSES:
        if groups.get(cls):
            print(f"\n{cls} ({len(groups[cls])}):")
            print("".join(f"- {who}: {why}\n" for who, why in sorted(groups[cls])), end="")
    for t, cmds in reached.items():
        was = before and any(t in r["entered"] for r in before["results"].values())
        print(f"\nConnected: {t}, entered by " + ", ".join(f"`{c}`" for c in cmds)
              + ("" if before is None else (" (it was entered before the change too)" if was
                                            else "; the snapshot before the change never entered it")))
    print("\nWIRE-GATE: done(" + ", ".join([f"{len(entered & set(funcs))} entered"]
                                           + [f"{len(groups[c])} {c}" for c in CLASSES if groups.get(c)]
                                           + [f"{len(reached)} connected"] * bool(reached)) + ")")
    return 0


def overview(repo):
    funcs, broken = inventory(repo)
    entries = declared_entries(repo)
    print(f"{len(py_files(repo))} Python files, {len(funcs)} functions"
          + (f", {len(broken)} that do not parse" if broken else ""))
    print("Declared ways in:")
    for name, kind, f, func in entries:
        print(f"- {kind}: {name}" + (f" -> {f}::{func}" if func else ""))
    loaders = runtime_loaders(repo)
    if loaders:
        print("Code picked by a name built at runtime (a snapshot sees these only if a command takes the path):")
        print("".join(f"- {x}\n" for x in loaders[:20]), end="")
    print('next: W --gate --run "<cmd>" --run "<cmd>" ...')
    return 0


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description="Record what really runs, and account for what does not.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--snapshot", action="store_true", help="run each --run command in a copy under the call tracer")
    ap.add_argument("--gate", action="store_true", help="check the stages; with --run, snapshot first")
    ap.add_argument("--run", action="append", default=[], help="a command that should reach code (repeat)")
    ap.add_argument("--target", action="append", default=[], help="FILE::FUNC you connected in this task (repeat)")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per command")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo)
    if a.snapshot:
        return take_snapshot(repo, a.run, a.timeout)
    if a.gate or a.run or a.target:
        return gate(repo, a.run, a.target, a.timeout)
    return overview(repo)


if __name__ == "__main__":
    sys.exit(main())
