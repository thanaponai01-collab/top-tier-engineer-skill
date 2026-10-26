#!/usr/bin/env python3
"""evolve.py - the mechanical side of the evolve-maintain skill.

A model that reads the code well makes the change it is asked for and runs the tests. What it
skips is the feature far from the change that reads what changed and that no test runs. This keeps
the tree as it was, records what each command prints on it, lists every reader of what changed, and
reruns every command on the changed tree.

  E                      keep the tree as it is now in .evolve/before/ (first call, before any
                         edit), then list the ways in and the recorded runs
  E --run CMD            run CMD in a throwaway copy of the kept tree under a call tracer and
                         record what it prints. Run it before or after the edit: it always runs on
                         the tree as it was
  E --gate               check the stages and print every problem with its fix:
    1 before   the tree as it was is kept, and at least one command is recorded on it
    2 reach    every function, script or config line that reads a name the change touched was
               entered by a recorded run, or has `- READER: out: <why>` in .evolve/notes.md
    3 hold     every recorded command prints on the changed tree what it printed before, or has
               `- run N: intended: <why>` in .evolve/notes.md

`E` is `python evolve.py <repo>`. Stdlib only.
"""
import argparse, ast, builtins, difflib, hashlib, json, keyword, os, re, shlex, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _encoding import utf8_streams  # noqa: E402

STATE = ".evolve"
BEFORE = f"{STATE}/before"
LEDGER = f"{STATE}/state.json"
NOTES = f"{STATE}/notes.md"
FILL = "[[fill"
# Folders that hold tools' state or caches, never the product: not scanned, copied or compared.
NOT_PRODUCT = {".git", "__pycache__", "node_modules", ".venv", "venv", STATE, ".debug", ".wire", ".latent",
               ".features", ".structure", ".threat", ".verify-state-cache", ".pytest_cache", ".mypy_cache",
               ".ruff_cache", ".perf", ".release"}
NOT_PRODUCT_FILES = {".verify-state.json"}
# Text a program reads at run time: a name in one of these is a reader. Prose is listed, not gated.
CONFIG = {".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".conf", ".env", ".sh", ".bash", ".ps1",
          ".bat", ".cmd", ".sql", ".tmpl", ".j2", ".jinja", ".html", ".js", ".mjs", ".ts", ".tsx", ".jsx",
          ".rb", ".go", ".php", ".java", ".kt", ".cs", ".rs", ".service", ".timer", ".cron", ".txt"}
PROSE = {".md", ".rst", ".adoc"}
BASH = shutil.which("bash")
WROTE_MAX = 20000   # characters of each written file kept for the comparison
# Names too common to say anything about who reads a change.
COMMON = set(dir(builtins)) | set(keyword.kwlist) | {"self", "cls", "args", "kwargs", "main", "run", "get",
                                                      "set", "data", "value", "name", "path", "result", "x",
                                                      "self", "__init__", "__name__", "__main__", "test"}

# An `out:` that says it was run: a run that entered the reader is seen by the tracer, so this one wasn't.
CLAIMS_RUN = re.compile(r"\b(covered|exercised|tested|run \d|runs? (it|this)|checked by|verified by)\b", re.IGNORECASE)

TRACER = r'''import atexit, os, sys, threading
_em_root = os.path.normcase(os.path.abspath(os.environ.get("EVOLVE_ROOT", ".")))
_em_seen = set()
_em_opened = set()
def _em_profile(frame, event, arg):
    if event == "call":
        _em_seen.add((frame.f_code.co_filename, frame.f_code.co_firstlineno, frame.f_code.co_name))
def _em_audit(event, args):
    if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        try:
            _em_opened.add(os.fsdecode(args[0]))
        except Exception:
            pass
def _em_dump():
    sys.setprofile(None)
    threading.setprofile(None)
    try:
        with open(os.environ["EVOLVE_CALL_LOG"], "a", encoding="utf-8") as fh:
            for f, line, name in list(_em_seen):
                p = os.path.normcase(os.path.abspath(f))
                if p.startswith(_em_root + os.sep):
                    fh.write(f"call\t{p}\t{line}\t{name}\n")
            for f in list(_em_opened):
                p = os.path.normcase(os.path.abspath(f))
                if p.startswith(_em_root + os.sep):
                    fh.write(f"open\t{p}\t0\t\n")
    except Exception:
        pass
sys.addaudithook(_em_audit)
sys.setprofile(_em_profile)
threading.setprofile(_em_profile)
atexit.register(_em_dump)
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


def normalize(text, root, tmp):
    for p in sorted({root, os.path.normcase(root), root.replace("\\", "/"), tmp, tmp.replace("\\", "/")},
                    key=len, reverse=True):
        text = text.replace(p, "<repo>")
    # Timings vary run to run: `Ran 3 tests in 0.002s`, `passed in 0.41s`, `took 12ms`.
    text = re.sub(r"\b(in|took) \d+(\.\d+)?\s?(s|ms|sec|seconds)\b", r"\1 <t>", text)
    text = re.sub(r"(?:/tmp|[A-Za-z]:\\[^\s'\"]*?\\Temp)[\\/][^\s'\"]+", "<tmp>", text)
    return text.replace("\r\n", "\n").rstrip()


def run_copy(src, cmd, timeout):
    """Run CMD under the tracer in a throwaway copy of SRC: (exit, output, entered, opened, wrote),
    where wrote is {rel path: text} for each file the run created or changed."""
    tmp = tempfile.mkdtemp(prefix="evolve-")
    try:
        root = os.path.join(tmp, "repo")
        copy_tree(src, root)
        start = product_files(root)
        hook = os.path.join(tmp, "hook")
        os.makedirs(hook)
        with open(os.path.join(hook, "sitecustomize.py"), "w", encoding="utf-8") as fh:
            fh.write(TRACER)
        log = os.path.join(hook, "calls.txt")
        # Git Bash rewrites an argument like `/v1/export` into a Windows path; a run must see what was typed.
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", EVOLVE_ROOT=root, EVOLVE_CALL_LOG=log,
                   MSYS_NO_PATHCONV="1", MSYS2_ARG_CONV_EXCL="*")
        env["PYTHONPATH"] = os.pathsep.join([hook, root] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
        # Agents write commands in the shell they use (`VAR=x cmd`, `&&`), so prefer bash.
        argv = [BASH, "-c", cmd] if BASH else cmd
        try:
            p = subprocess.run(argv, cwd=root, shell=not BASH, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout, env=env)
            code, text = p.returncode, (p.stdout or "") + (p.stderr or "")
        except subprocess.TimeoutExpired:
            code, text = "timeout", "timed out"
        entered, opened = set(), set()
        base = os.path.normcase(os.path.abspath(root))
        try:
            with open(log, encoding="utf-8") as fh:
                for row in fh:
                    kind, path, line, name = (row.rstrip("\n").split("\t") + ["", "", "", ""])[:4]
                    r = rel(path, base)
                    if kind == "call" and line.isdigit():
                        entered.add((r, "<module>" if name == "<module>" else int(line)))
                    elif kind == "open":
                        opened.add(r)
        except OSError:
            pass
        wrote = {}
        for r, sha in product_files(root).items():
            if start.get(r) != sha:
                with open(os.path.join(root, *r.split("/")), "rb") as fh:
                    wrote[r] = normalize(fh.read()[:WROTE_MAX].decode("utf-8", "replace"), root, tmp)
        for r in set(start) - set(product_files(root)):
            wrote[r] = "<deleted>"
        return code, normalize(text, root, tmp), entered, opened, wrote
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def tail(text, n=4):
    return [ln[:200] for ln in text.splitlines() if ln.strip()][-n:]


def outside_paths(repo, cmd):
    """Absolute paths in CMD that are not inside the repo: a run that depends on one does not rerun."""
    try:
        tokens = shlex.split(cmd, posix=os.name != "nt")
    except ValueError:
        tokens = cmd.split()
    out = []
    for t in tokens:
        t = t.strip("'\"")
        if not (t.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", t)) or t == "/dev/null":
            continue
        # A URL path (`/v2/export?fmt=csv`) is an argument, not a file: only a path whose folder is there.
        parent = os.path.dirname(t.rstrip("/\\"))
        if os.path.exists(t) or (parent not in ("", "/") and os.path.isdir(parent)):
            if not os.path.normcase(os.path.abspath(t)).startswith(os.path.normcase(repo) + os.sep):
                out.append(t)
    return out


# ---------------- what changed, and who reads it ---------------------------------
def is_test_file(r):
    parts = r.split("/")
    return any(p in ("tests", "test") for p in parts[:-1]) or bool(
        re.match(r"^(test_.+|.+_test|conftest)\.py$", parts[-1]))


def parse(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        return src, ast.parse(src)
    except (OSError, SyntaxError, ValueError):
        return None, None


def units(path):
    """{qualname: (first line, source hash, node)} for every function and method, plus `<module>`
    for the statements outside them. None when the file does not parse."""
    src, tree = parse(path)
    if tree is None:
        return None
    out, lines = {}, src.splitlines()

    def seg(node):
        start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
        return start, "\n".join(lines[start - 1:node.end_lineno])

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start, text = seg(child)
                out[prefix + child.name] = (start, hashlib.sha256(text.encode()).hexdigest()[:16], child)
                walk(child, prefix + child.name + ".")
            elif isinstance(child, ast.ClassDef):
                walk(child, prefix + child.name + ".")
    walk(tree, "")
    module_body = [n for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    mod_text = "\n".join(ast.unparse(n) for n in module_body if not isinstance(n, ast.ClassDef)) + "\n" + \
        "\n".join(ast.unparse(n) for c in module_body if isinstance(c, ast.ClassDef) for n in c.body
                  if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
    out["<module>"] = (0, hashlib.sha256(mod_text.encode()).hexdigest()[:16], tree)
    return out


def names_in(node, skip_defs=True):
    """Identifiers, attribute names and string constants a node mentions (not inside nested defs
    when it is a module)."""
    found, strings = set(), set()
    stack = [node]
    while stack:
        n = stack.pop()
        for child in ast.iter_child_nodes(n):
            if skip_defs and isinstance(n, ast.Module) and isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if skip_defs and isinstance(n, ast.ClassDef) and isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if isinstance(child, ast.Name):
                found.add(child.id)
            elif isinstance(child, ast.Attribute):
                found.add(child.attr)
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
                for a in child.names:
                    found.update(a.name.split("."))
                if isinstance(child, ast.ImportFrom) and child.module:
                    found.update(child.module.split("."))
            elif isinstance(child, ast.Constant) and isinstance(child.value, str):
                strings.add(child.value)
            stack.append(child)
    return found, strings


def changes(before, now):
    """(changed files, touched names, removed string literals, changed units {file::qual})."""
    was, cur = product_files(before), product_files(now)
    changed = sorted(f for f in set(was) | set(cur) if was.get(f) != cur.get(f))
    names, literals, touched = set(), set(), []
    for f in changed:
        stem = os.path.splitext(os.path.basename(f))[0]
        if not f.endswith(".py") or is_test_file(f):
            continue
        old = units(os.path.join(before, *f.split("/"))) if f in was else {}
        new = units(os.path.join(now, *f.split("/"))) if f in cur else {}
        old, new = old or {}, new or {}
        if f not in cur:
            names.add(stem)
        for q in set(old) | set(new):
            if q == "<module>":
                continue
            if (old.get(q) or (0, None))[1] != (new.get(q) or (0, None))[1]:
                touched.append(f"{f}::{q}")
                names.add(q.rsplit(".", 1)[-1])
        if (old.get("<module>") or (0, None))[1] != (new.get("<module>") or (0, None))[1]:
            touched.append(f"{f}::<module>")
            o_names, o_str = names_in(old["<module>"][2]) if "<module>" in old else (set(), set())
            n_names, n_str = names_in(new["<module>"][2]) if "<module>" in new else (set(), set())
            names |= {n for n in o_names ^ n_names}
            literals |= {s for s in o_str - n_str if len(s) >= 3 and not s.isspace()}
        for q in set(old) - set(new):
            if q != "<module>":
                literals |= {s for s in names_in(old[q][2], skip_defs=False)[1] if len(s) >= 4 and "/" in s}
    names = {n for n in names if n not in COMMON and len(n) >= 3 and not n.startswith("__")}
    return changed, names, literals, touched


def readers(before, names, literals, touched):
    """{reader id: {file, unit, line, why}} on the tree as it was: every function, module body or
    config line that mentions a touched name or a removed literal, outside the touched units."""
    out = {}
    if not names and not literals:
        return out
    word = re.compile(r"(?<![\w.])(" + "|".join(re.escape(n) for n in sorted(names)) + r")(?!\w)") if names else None
    for p in walk_files(before):
        r = rel(p, before)
        ext = os.path.splitext(r)[1].lower()
        if ext == ".py":
            if is_test_file(r):
                continue
            us = units(p)
            if not us:
                continue
            for q, (line, _, node) in us.items():
                if f"{r}::{q}" in touched:
                    continue
                found, strings = names_in(node)
                hit = sorted(found & names) + sorted(s for s in strings for lit in literals if lit in s)
                if hit:
                    out[f"{r}::{q}"] = {"file": r, "unit": q, "line": line,
                                        "why": "reads " + ", ".join(dict.fromkeys(hit))[:80]}
        elif ext in CONFIG or ext in PROSE:
            try:
                with open(p, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                hit = [lit for lit in literals if lit in line] or (word.findall(line) if word else [])
                if hit:
                    out[f"{r}:{i}"] = {"file": r, "unit": None, "line": i, "prose": ext in PROSE,
                                       "why": "names " + ", ".join(dict.fromkeys(hit))[:80]}
    return out


def entered(reader, runs):
    """The recorded runs (numbers) that entered this reader on the tree as it was."""
    hits = []
    for run in runs:
        calls = {(f, ln) for f, ln in run.get("entered", [])}
        if reader["unit"] is None:
            ok = reader["file"] in run.get("opened", []) or reader["file"] in run["cmd"]
        elif reader["unit"] == "<module>":
            ok = (reader["file"], "<module>") in calls or reader["file"] in run["cmd"]
        else:
            ok = (reader["file"], reader["line"]) in calls
        if ok:
            hits.append(run["n"])
    return hits


# ---------------- notes -----------------------------------------------------------
def read_notes(repo):
    """({reader: reason}, {run n: reason}, text) for `- X: out: <why>` and `- run N: intended: <why>`."""
    outs, intended, text = {}, {}, ""
    try:
        with open(os.path.join(repo, NOTES), encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return outs, intended, text
    for line in text.splitlines():
        m = re.match(r"^\s*-\s*run\s+(\d+)\s*:\s*intended\s*:\s*(.*)$", line, re.IGNORECASE)
        if m:
            intended[int(m.group(1))] = m.group(2).strip()
            continue
        m = re.match(r"^\s*-\s*`?([^`\s]+?)`?\s*[:|]\s*out\s*:\s*(.*)$", line)
        if m:
            outs[m.group(1)] = m.group(2).strip()
            continue
        m = re.match(r"^\s*-\s*`?([^`\s]+?)`?\s*[:|]\s*(\[\[fill.*)$", line)
        if m:
            outs.setdefault(m.group(1), m.group(2).strip())
    return outs, intended, text


def append_slots(repo, lines, text):
    if not lines:
        return 0
    head = "" if text else ("# Change notes\n\nA reader no recorded run entered: `- READER: out: <why the change "
                            "cannot reach what it does>`.\nA run whose output changed on purpose: "
                            "`- run N: intended: <what the user asked for that changes it>`.\n\n")
    sep = "" if not text or text.endswith("\n") else "\n"
    path = os.path.join(repo, NOTES)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(head + sep + "\n".join(lines) + "\n")
    return len(lines)


# ---------------- commands --------------------------------------------------------
def keep(repo):
    before = os.path.join(repo, BEFORE)
    if os.path.isdir(before):
        return False
    copy_tree(repo, before)
    return True


def record(repo, cmd, timeout):
    if not cmd.strip():
        print('RUN: give the command a user or a job runs: E --run "python app.py report"')
        return 2
    outside = outside_paths(repo, cmd)
    if outside:
        print(f"RUN: {', '.join(outside)} is outside the repo. Write files to a relative path (it lands in a "
              "throwaway copy), so the run repeats on the changed tree.")
        return 2
    if keep(repo):
        print(f"(kept the tree as it is now in {BEFORE}/: every run executes there. If you already edited, "
              f"delete {STATE}/, undo the edit, and start again)")
    before = os.path.join(repo, BEFORE)
    code, out, ent, opened, wrote = run_copy(before, cmd, timeout)
    code2, out2, _, _, wrote2 = run_copy(before, cmd, timeout)
    print(f"RUN: exit {code}  {cmd}")
    print("".join(f"  | {ln}\n" for ln in tail(out, 6)), end="")
    if (code, out, wrote) != (code2, out2, wrote2):
        print("RUN: not recorded: it printed or wrote something different the second time on the same tree. "
              "Make it deterministic (fixed dates, seeds, sorted output) or leave out the part that varies.")
        return 1
    if not ent and not opened:
        print("RUN: not recorded: it entered no code in the repo. Run the product's own command.")
        return 1
    ledger = read_json(repo, LEDGER, {})
    runs = [r for r in ledger.get("runs", []) if r["cmd"] != cmd]
    n = max([r["n"] for r in ledger.get("runs", [])] + [0]) + 1
    entry = {"n": n, "cmd": cmd, "exit": code, "out": out, "wrote": wrote,
             "entered": sorted([list(e) for e in ent], key=str), "opened": sorted(opened)}
    ledger["runs"] = sorted(runs + [entry], key=lambda r: r["n"])
    save(repo, ledger)
    print(f"RUN {n}: recorded on the tree as it was ({len(ent)} functions entered"
          + (f"; wrote {', '.join(sorted(wrote))}" if wrote else "") + ")")
    print("next: record a run for each way in that reads what you will change, make the change, then E --gate")
    return 0


def first_diff(a, b, what):
    """`what line N was X, now Y` at the first block that differs, or None when A == B."""
    if a == b:
        return None
    al, bl = a.splitlines(), b.splitlines()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, al, bl, autojunk=False).get_opcodes():
        if tag != "equal":
            def show(lines):
                return " / ".join(ln.strip()[:60] for ln in lines[:3]) or "<nothing>"
            return f"{what} line {i1 + 1} was `{show(al[i1:i2])}`, now `{show(bl[j1:j2])}`"
    return f"{what} differs"


def gate(repo, timeout):
    ledger = read_json(repo, LEDGER, {})
    runs = ledger.get("runs", [])
    problems = {1: [], 2: [], 3: []}
    print('E = python "' + os.path.abspath(__file__) + '" ' + repo)
    before = os.path.join(repo, BEFORE)
    if not os.path.isdir(before):
        problems[1].append(f"no kept tree. Run E before your first edit: it copies the tree to {BEFORE}/")
    elif not runs:
        problems[1].append('no command recorded on the tree as it was. Record what a user or job runs: '
                           'E --run "<command>"')
    changed, names, literals, touched, reach = [], set(), set(), [], {}
    outs, intended, text = read_notes(repo)
    if os.path.isdir(before):
        changed, names, literals, touched = changes(before, repo)
        if not changed:
            problems[2].append("no product file differs from the kept tree. Make the change, then E --gate")
        reach = readers(before, names, literals, touched)
        gated = {k: v for k, v in reach.items() if not v.get("prose")}
        missing = []
        for k, info in sorted(gated.items()):
            if entered(info, runs):
                continue
            reason = outs.get(k, "")
            if not reason:
                missing.append(f"- {k}: {FILL}: out: <why the change cannot reach what it does>, "
                               "or record a run that enters it]]")
                problems[2].append(f"{k} ({info['why']}): no recorded run entered it. Record a run that does "
                                   f"(E --run \"<command>\"), or fill its line in {NOTES}")
            elif reason.startswith(FILL):
                problems[2].append(f"{k} ({info['why']}): no recorded run entered it and its line in {NOTES} "
                                   "is unfilled. Record a run that enters it, or fill `out: <why>`")
            elif len(reason.split()) < 4:
                problems[2].append(f"{k}: `out: {reason}` says too little. Say why the change cannot reach "
                                   "what it does, or record a run that enters it")
            elif CLAIMS_RUN.search(reason):
                problems[2].append(f"{k}: `out: {reason[:70]}` says a run or test covers it, but no recorded "
                                   "run entered it (the tracer sees every function a run calls). Record the run "
                                   "that does, or say why the change cannot reach it")
        added = append_slots(repo, missing, text)
        if added:
            print(f"(appended {added} slot{'s' if added != 1 else ''} to {NOTES})")
        for k in sorted(outs):
            if k not in gated:
                problems[2].append(f"{NOTES} has a line for {k}, which is not a reader of this change. Delete it")

    diffs = []
    if runs and changed:
        for run in runs:
            code, out, _, _, wrote = run_copy(repo, run["cmd"], timeout)
            run["now_exit"], run["now_out"] = code, out
            was_wrote = run.get("wrote", {})
            if (code, out, wrote) == (run["exit"], run["out"], was_wrote):
                continue
            diffs.append(run)
            reason = intended.get(run["n"], "")
            if reason and len(reason.split()) >= 4:
                continue
            first = first_diff(run["out"], out, "output")
            for f in sorted(set(was_wrote) | set(wrote)):
                if was_wrote.get(f) != wrote.get(f):
                    first = first or first_diff(was_wrote.get(f, "<not written>"), wrote.get(f, "<not written>"),
                                                f"wrote {f}")
            first = first or f"exit {run['exit']} -> {code}"
            problems[3].append(f"run {run['n']} `{run['cmd']}` changed: exit {run['exit']} -> {code}; {first}. "
                               f"Fix it, or if the user asked for this, add `- run {run['n']}: intended: <why>` "
                               f"to {NOTES}")
        save(repo, ledger)
    for n in sorted(intended):
        if n not in {r["n"] for r in diffs}:
            problems[3].append(f"{NOTES} says run {n} changes on purpose, but it prints what it printed before. "
                               "Delete the line")

    names_line = {1: "before: the tree as it was is kept, with commands recorded on it",
                  2: "reach: every reader of the change entered by a run, or accounted for",
                  3: "hold: every recorded command prints what it printed before, or the change is intended"}
    for g in (1, 2, 3):
        print(f"STAGE {g} {names_line[g]}: " + ("holds" if not problems[g] else f"open, {len(problems[g])} to fix"))
        for line in problems[g]:
            print(f"  - {line}")
    open_stages = [g for g in (1, 2, 3) if problems[g]]
    if open_stages:
        print(f"EVOLVE-GATE: open({', '.join(map(str, open_stages))}): fix the lines above, then E --gate")
        return 1
    answer(runs, changed, touched, reach, outs, intended, diffs)
    return 0


def answer(runs, changed, touched, reach, outs, intended, diffs):
    gated = {k: v for k, v in reach.items() if not v.get("prose")}
    prose = sorted(k for k, v in reach.items() if v.get("prose"))
    print("\nANSWER (drafted from the recorded runs; give it, adding only context):\n")
    print(f"Changed: {', '.join(changed)} ({len(touched)} functions or module bodies).")
    hit = {k: entered(v, runs) for k, v in gated.items()}
    print(f"Reach: {len(gated)} readers of what changed on the tree as it was; "
          f"{sum(1 for v in hit.values() if v)} entered by a recorded run, "
          f"{sum(1 for v in hit.values() if not v)} out of reach:")
    for k, ns in sorted(hit.items()):
        print(f"- {k} ({gated[k]['why']}): " + (f"run {', '.join(map(str, ns))}" if ns else f"out: {outs.get(k, '')}"))
    same = len(runs) - len(diffs)
    print(f"Runs: {len(runs)} commands recorded before the change; {same} print the same after it"
          + (f"; {len(diffs)} changed on purpose:" if diffs else "."))
    for r in diffs:
        print(f"- run {r['n']} `{r['cmd']}`: {intended.get(r['n'], '')}")
    if prose:
        print(f"Docs that name what changed (check they still say what is true): {', '.join(prose[:10])}.")
    print("Broke along the way and fixed: [[fill: each run that went wrong on the changed tree before you "
          "fixed it, and why, or 'nothing']]")
    print("Not covered: [[fill: callers outside this repo, data already stored, and what no run reached]]")
    print(f"\nEVOLVE-GATE: done({len(runs)} runs, {same} unchanged, {len(diffs)} intended, "
          f"{sum(1 for v in hit.values() if v)}/{len(gated)} readers run)")


def overview(repo, timeout):
    kept = keep(repo)
    ledger = read_json(repo, LEDGER, {})
    if kept:
        print(f"Kept the tree as it is now in {BEFORE}/. Make your change after this; every recorded run "
              "executes on that copy.")
    ways = []
    for p in walk_files(repo):
        r = rel(p, repo)
        if r.endswith(".py") and not is_test_file(r):
            src, tree = parse(p)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.If) and "__main__" in ast.dump(node.test):
                    ways.append(f"{r} (script)")
                    break
            subs = [n.args[0].value for n in ast.walk(tree) if isinstance(n, ast.Call)
                    and getattr(n.func, "attr", "") == "add_parser" and n.args
                    and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)]
            if subs:
                ways.append(f"{r} subcommands: {', '.join(subs)}")
    print("Ways in found: " + ("; ".join(ways) if ways else "none (name the commands users and jobs run)"))
    for r in ledger.get("runs", []):
        print(f"run {r['n']} exit {r['exit']}: `{r['cmd']}`")
    print('next: E --run "<command>" for each way in that reads what you will change; change; E --gate')
    return 0


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description="Keep the tree as it was, record what it does, rerun after the change.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--run", metavar="CMD", help="a command a user or job runs; recorded on the tree as it was")
    ap.add_argument("--gate", action="store_true", help="check the three stages")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per command")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo)
    if a.run is not None:
        return record(repo, a.run, a.timeout)
    if a.gate:
        return gate(repo, a.timeout)
    return overview(repo, a.timeout)


if __name__ == "__main__":
    sys.exit(main())
