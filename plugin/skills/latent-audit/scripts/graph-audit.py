#!/usr/bin/env python3
"""graph-audit.py — the mechanical invoker behind the latent-audit skill.

Builds ONE module-level import/reference graph over a source tree and answers
three questions from it, each with its honest evidence ceiling:

  1. LAYER BREACHES  (proven)    — given a declared layer order, which import
                                   edges point the wrong way (upward)?
  2. DEAD MODULES    (suspected) — which modules does nothing in-tree import
                                   or reference?  Static absence is NOT proof
                                   of death; deletion requires a disconnection
                                   proof (see latent-audit SKILL.md).
  3. UNUSED DEFS     (suspected) — which top-level functions/classes are
                                   defined but never referenced in-tree?

Stdlib only.  Python-deep; the report says exactly where depth stops rather
than dressing shallow up as uniform.

Two things a reading of the code cannot settle are done here instead:

  MAPPED  - a file a feature in the repo's FEATURES.md names (`feature-map`) is live, whatever the
            import graph says: the map recorded a way in.
  --try-delete FILE ...
          - deletes the files in a throwaway copy and runs, before and after, everything recorded
            that could notice: the map's recorded runs (`.features/features.py check --rerun`),
            VERIFY.md's checks (`verify-loop`), the unit tests, and each `--run CMD` you name (a
            command you found that reaches the code, e.g. the job runner that loads it by name).
            A check that passed before and fails after means the code is live.

  --gate  - the four gates a cleanup must pass, checked from .latent/ in the repo: every
            suspect has a verdict, every verdict has proof, the deletions on disk match the
            proof, and the answer drafted from it. Prints what is missing; `done` when all hold.

Usage:
  python3 scripts/graph-audit.py <path> [<path> ...]
        [--layers LAYERS_FILE] [--entry MODULE ...] [--json] [--edges FILE]
  python3 scripts/graph-audit.py <repo> --try-delete FILE [FILE ...] [--run CMD ...]
  python3 scripts/graph-audit.py <repo> --gate

--edges FILE writes the import graph as JSON ({"modules": {name: path},
"edges": [{"from", "to", "line"}]}) for other skills' tools to read; the
report is unchanged.

Layers file format (top layer first; a module may import SAME or LOWER
layers, never a HIGHER one), '#' comments allowed:

    interface: app/routes/, app/cli/
    domain:    app/services/
    data:      app/models/, app/db/

Summary line:
  LATENT: clean(N modules traced)
        | findings(dead: A, unused: B, layer-breaches: C)
        | blocked(no analyzable source)

`clean` requires that every dimension was actually MEASURED. Without `--layers` the layer
dimension is not measured, so the verdict reports `layer-breaches: UNMEASURED(...)` rather
than `0` and never claims `clean` (a region the analyzer could not enter is
UNKNOWN, never folded into a clean result). The EXIT CODE stays 0 in that case:
an unmeasured dimension is a gap in how the tool was invoked, not a defect in the subject,
and failing by default would make this a permanently-red gate — which is a disabled gate.
"""

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from _encoding import utf8_streams

PY_EXT = {".py"}
# Text files swept for raw-name references (configs, templates, scripts...):
TEXT_EXT = {".py", ".pyi", ".txt", ".md", ".yml", ".yaml", ".toml", ".cfg",
            ".ini", ".json", ".html", ".js", ".ts", ".jsx", ".tsx", ".sh",
            ".xml", ".env", ".service"}
TEXT_NAMES = {"dockerfile", "makefile", "procfile"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", ".latent",
             "build", ".tox", ".mypy_cache", ".pytest_cache", ".blast", ".mistakes"}

# Modules assumed reachable even with zero in-edges (framework/tooling entry):
ENTRY_BASENAMES = {"main", "app", "application", "cli", "manage", "wsgi",
                   "asgi", "setup", "conftest", "__main__", "__init__"}


def iter_files(roots, wanted_ext=None):
    for root in roots:
        if os.path.isfile(root):
            yield root
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for f in filenames:
                p = os.path.join(dirpath, f)
                ext = os.path.splitext(f)[1].lower()
                if wanted_ext is None or ext in wanted_ext \
                        or f.lower() in TEXT_NAMES:
                    yield p


def module_name(path, roots):
    """Dotted module name relative to the nearest analyzed root."""
    ap = os.path.abspath(path)
    best = ""
    for r in roots:
        ar = os.path.abspath(r)
        base = ar if os.path.isdir(ar) else os.path.dirname(ar)
        if ap.startswith(base) and len(base) > len(best):
            best = base
    rel = os.path.relpath(ap, best) if best else os.path.basename(ap)
    rel = os.path.splitext(rel)[0]
    return rel.replace(os.sep, ".")


def parse_tree(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return ast.parse(fh.read())
    except (OSError, UnicodeDecodeError, SyntaxError):
        return None


def build_graph(pyfiles, roots):
    """modules: name -> path; edges: importer -> {(imported, lineno)}."""
    modules = {module_name(p, roots): p for p in pyfiles}
    # index by trailing segments so `from services.auth import x` resolves
    # to `app.services.auth` when unambiguous
    tail_index = defaultdict(set)
    for m in modules:
        parts = m.split(".")
        for i in range(len(parts)):
            tail_index[".".join(parts[i:])].add(m)

    def resolve(name):
        if name in modules:
            return name
        hits = tail_index.get(name, ())
        return next(iter(hits)) if len(hits) == 1 else None

    edges = defaultdict(set)
    asts = {}
    for mod, path in modules.items():
        tree = parse_tree(path)
        if tree is None:
            continue
        asts[mod] = tree
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                names = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                names = [n.module] + [n.module + "." + a.name
                                      for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.level:
                pkg = mod.split(".")[:-n.level]
                base = ".".join(pkg + ([n.module] if n.module else []))
                names = [base] + [base + "." + a.name for a in n.names]
            else:
                continue
            for name in names:
                probe = name
                while probe:
                    target = resolve(probe)
                    if target and target != mod:
                        edges[mod].add((target, n.lineno))
                        break
                    probe = ".".join(probe.split(".")[:-1])
    return modules, edges, asts


# ---------------- check 1: layer breaches (proven) --------------------------
def load_layers(path):
    layers = []  # [(name, [prefixes])] top first
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            name, globs = line.split(":", 1)
            prefixes = [g.strip().strip("/").replace("/", ".")
                        for g in globs.split(",") if g.strip()]
            layers.append((name.strip(), prefixes))
    return layers


def layer_of(mod, layers):
    for i, (name, prefixes) in enumerate(layers):
        for p in prefixes:
            if mod == p or mod.startswith(p + "."):
                return i, name
    return None, None


def check_layers(modules, edges, layers):
    breaches, unmapped = [], sorted(
        m for m in modules if layer_of(m, layers)[0] is None)
    for src, targets in edges.items():
        si, sname = layer_of(src, layers)
        if si is None:
            continue
        for dst, lineno in targets:
            di, dname = layer_of(dst, layers)
            if di is not None and di < si:  # importing a HIGHER layer
                breaches.append({
                    "file": modules[src], "line": lineno,
                    "edge": f"{src} ({sname}) -> {dst} ({dname})",
                    "rule": f"layer '{sname}' may not import layer '{dname}'"})
    return breaches, unmapped


# ---------------- raw-text reference sweep ----------------------------------
def raw_reference_hits(roots, needles):
    """For each needle (a bare name), count files whose text contains it,
    excluding the file that defines it (caller filters)."""
    hits = defaultdict(set)
    live = [n for n in needles if len(n) >= 3]  # short names = pure noise
    for path in iter_files(roots, TEXT_EXT):
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except OSError:
            continue
        for n in live:
            if n in text:
                hits[n].add(os.path.abspath(path))
    return hits


# ---------------- the feature map (feature-map's FEATURES.md) ----------------
HERE = os.path.dirname(os.path.abspath(__file__))
SIBLING = os.path.join(os.path.dirname(os.path.dirname(HERE)), "{0}", "scripts", "{1}")


def load_script(*candidates):
    """Import a sibling skill's helper by path: this plugin's copy first, then the repo's own."""
    for path in candidates:
        if os.path.isfile(path):
            spec = importlib.util.spec_from_file_location(
                "_la_" + os.path.splitext(os.path.basename(path))[0], path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    return None


def mapped_files(repo):
    """{repo-relative path: feature name} for every file FEATURES.md names (entry points and
    trace steps, `## Not features` included); {} when the repo has no map."""
    if not os.path.isfile(os.path.join(repo, "FEATURES.md")):
        return {}
    fm = load_script(SIBLING.format("feature-map", "features.py"),
                     os.path.join(repo, ".features", "features.py"))
    if fm is None:
        return {}
    out = {}
    for f in fm.parse(fm.load(repo, "FEATURES.md")):
        for rel in fm.feature_files(f):
            rel = rel.replace("\\", "/")
            out.setdefault(rel[2:] if rel.startswith("./") else rel, f["name"])
    return out


def mapped_entry_files(repo):
    """The files FEATURES.md declares entry points in: where the program starts, not code that
    only looks dead."""
    fm = load_script(SIBLING.format("feature-map", "features.py"),
                     os.path.join(repo, ".features", "features.py"))
    if fm is None or not os.path.isfile(os.path.join(repo, "FEATURES.md")):
        return set()
    return {rel.replace("\\", "/").lstrip("./") for f in fm.parse(fm.load(repo, "FEATURES.md"))
            for _k, _a, rel, _n in f["entries"] if rel}


def rel_to(path, repo):
    return os.path.relpath(os.path.abspath(path), os.path.abspath(repo)).replace(os.sep, "/")


# ---------------- check 2: dead modules (suspected) --------------------------
def check_dead_modules(modules, edges, roots, declared_entries, mapped=None, repo=".", rescue=True):
    imported = {dst for targets in edges.values() for dst, _ in targets}
    candidates = []
    for mod, path in modules.items():
        base = mod.split(".")[-1]
        if mapped and rel_to(path, repo) in mapped:
            continue
        if mod in imported or base in ENTRY_BASENAMES \
                or base.startswith("test") or base in declared_entries \
                or mod in declared_entries:
            continue
        candidates.append(mod)
    if not rescue:  # the gate: text mentions are judged by name_mention, not silently dropped
        return [{"module": m, "file": modules[m]} for m in sorted(candidates)
                if "__main__" not in (read_text(modules[m]))]
    # rescue candidates referenced by raw text anywhere else in the tree
    hits = raw_reference_hits(roots, {m.split(".")[-1] for m in candidates})
    dead = []
    for mod in sorted(candidates):
        base = mod.split(".")[-1]
        refs = hits.get(base, set()) - {os.path.abspath(modules[mod])}
        if not refs:
            dead.append({"module": mod, "file": modules[mod]})
    return dead


# ---------------- check 3: unused defs (suspected) ---------------------------
def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def check_unused_defs(modules, asts, roots):
    defs = []  # (name, mod, path, lineno)
    for mod, tree in asts.items():
        if os.path.basename(modules[mod]).startswith("test"):
            continue  # test runners discover these by reflection
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                name = node.name
                if name.startswith("__") or name.startswith("test") \
                        or getattr(node, "decorator_list", None):
                    continue  # dunder / test / framework-wired via decorator
                defs.append((name, mod, modules[mod], node.lineno))
    hits = raw_reference_hits(roots, {d[0] for d in defs})
    unused = []
    for name, mod, path, lineno in sorted(defs):
        refs = hits.get(name, set()) - {os.path.abspath(path)}
        if not refs:
            # also require ≤1 occurrence in its own file (the def itself)
            try:
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    if fh.read().count(name) > 1:
                        continue
            except OSError:
                continue
            unused.append({"name": name, "module": mod,
                           "file": path, "line": lineno})
    return unused


# ---------------- try-delete: what breaks without it ------------------------
COPY_IGNORE = shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".venv", "venv", "*.pyc")


def recorded_checks(repo, extra):
    """[(label, command, shell)] that could notice a deletion, found in the repo, plus --run."""
    checks = []
    if os.path.isfile(os.path.join(repo, "FEATURES.md")) \
            and os.path.isfile(os.path.join(repo, ".features", "features.py")):
        checks.append(("map: recorded runs (features.py check --rerun)",
                       [sys.executable, os.path.join(".features", "features.py"), "check", "--rerun"], False))
    verify = SIBLING.format("verify-loop", "verify.py")
    if os.path.isfile(os.path.join(repo, "VERIFY.md")) and os.path.isfile(verify):
        checks.append(("verify: VERIFY.md checks (verify.py run)", [sys.executable, verify, "run", "."], False))
    has_tests = any(n.startswith("test") and n.endswith(".py")
                    for d, _s, names in os.walk(repo) if not set(d.split(os.sep)) & SKIP_DIRS
                    for n in names)
    if has_tests:
        checks.append(("tests: python -m unittest discover",
                       [sys.executable, "-m", "unittest", "discover", "-q"], False))
    checks += [(f"run: {cmd}", cmd, True) for cmd in extra]
    return checks


PROBLEM = re.compile(r"FAILS|STALE|BROKEN|Error|FAIL:|FAILED")


IMPORT_HOOK = """import atexit, os, sys
def _latent_dump():
    try:
        with open(os.environ["LATENT_IMPORT_LOG"], "a", encoding="utf-8") as fh:
            for m in list(sys.modules.values()):
                f = getattr(m, "__file__", None)
                if f:
                    fh.write(os.path.abspath(f) + "\\n")
    except Exception:
        pass
atexit.register(_latent_dump)
"""


def run_checks(repo, checks, delete=(), imports=None):
    """{label: (exit code, problem lines)} for every check, run in a throwaway copy of repo with
    `delete` removed, so the repo itself is never touched. Problem lines are the output lines that
    name a failure, with the copy's path removed, so two runs can be compared line by line.
    With `imports` (a dict), every Python process a check starts logs the modules it loaded, and
    imports[label] becomes the set of repo files that check imported: observed, not inferred."""
    tmp = tempfile.mkdtemp(prefix="latent-try-")
    copy = os.path.join(tmp, "repo")
    try:
        shutil.copytree(repo, copy, ignore=COPY_IGNORE)
        for rel in delete:
            target = os.path.join(copy, *rel.replace("\\", "/").split("/"))
            if os.path.isdir(target):
                shutil.rmtree(target)
            elif os.path.exists(target):
                os.remove(target)
        out = {}
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", VERIFY_STATE_DIR=os.path.join(tmp, "state"))
        if imports is not None:
            hook = os.path.join(tmp, "hook")
            os.makedirs(hook)
            with open(os.path.join(hook, "sitecustomize.py"), "w", encoding="utf-8") as fh:
                fh.write(IMPORT_HOOK)
            env["PYTHONPATH"] = hook + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        for i, (label, cmd, shell) in enumerate(checks):
            if imports is not None:
                env["LATENT_IMPORT_LOG"] = os.path.join(tmp, f"imports-{i}.txt")
            try:
                p = subprocess.run(cmd, cwd=copy, shell=shell, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=300, env=env)
                text = ((p.stdout or "") + (p.stderr or "")).replace(copy, "<repo>")
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()] or [""]
                out[label] = (p.returncode, [ln for ln in lines if PROBLEM.search(ln)] or lines[-1:])
            except subprocess.TimeoutExpired:
                out[label] = ("timeout", ["timed out"])
            if imports is not None:
                imports[label] = loaded_files(env["LATENT_IMPORT_LOG"], copy)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def loaded_files(log, copy):
    """The repo-relative files an import log names, ignoring the stdlib and anything outside."""
    root = os.path.normcase(os.path.abspath(copy))
    out = set()
    try:
        with open(log, encoding="utf-8") as fh:
            for line in fh:
                f = os.path.normcase(os.path.abspath(line.strip()))
                if f.startswith(root + os.sep):
                    out.add(os.path.relpath(f, root).replace(os.sep, "/"))
    except OSError:
        pass
    return out


def new_problems(b, a):
    """What the deletion broke in one check: everything, if it passed before; otherwise only the
    failure lines it did not print before (an already-red map still notices a new FAILS line)."""
    if a[0] == 0:
        return []
    if b[0] == 0:
        return a[1]
    return [ln for ln in a[1] if ln not in b[1]]


def broken_by(before, after):
    return [(label, why[-1][:160]) for label in after
            for why in [new_problems(before[label], after[label])] if why]


def try_delete(repo, files, extra):
    """Print what deleting `files` breaks; return 1 breaks, 0 nothing recorded breaks,
    2 nothing recorded could notice (unchecked, or weak: unit tests only)."""
    missing = [f for f in files if not os.path.exists(os.path.join(repo, f))]
    if missing:
        print("not found in the repo: " + ", ".join(missing))
        print("DELETE-CHECK: blocked(paths are relative to the repo root)")
        return 2
    checks = recorded_checks(repo, extra)
    if not checks:
        print("No map (FEATURES.md + .features/), no VERIFY.md, no tests and no --run command: "
              "nothing recorded could notice this deletion. Find what reaches the code (a loader, a "
              "schedule, a config entry) and name the command that runs it with --run.")
        print("DELETE-CHECK: unchecked(nothing could notice)")
        return 2
    ensure_inventory(repo)
    before = run_checks(repo, checks)
    after = run_checks(repo, checks, files)
    print(f"DELETE-CHECK of {len(files)} file(s), each check run before and after in a throwaway copy:")
    for label in after:
        why = new_problems(before[label], after[label])
        state = ("BREAKS" if why else "still passes" if after[label][0] == 0 else
                 "already failing, nothing new")
        print(f"  {state:<29} {label}" + (f"  ({why[-1][:160]})" if why else ""))
    broken = broken_by(before, after)
    per_file = {f: broken for f in files}
    if broken and len(files) > 1:
        print("Which file breaks it, each deleted alone:")
        for f in files:
            alone = broken_by(before, run_checks(repo, checks, [f]))
            per_file[f] = alone
            print(f"  {'LIVE' if alone else 'ok':<5} {f}" + (f"  breaks: {alone[0][0]}" if alone else ""))
    useful = [label for label in before if before[label][0] == 0 or label.startswith("map:")]
    group = ("unchecked" if not useful else
             "weak" if all(label.startswith("tests:") for label in useful) else "nothing-breaks")
    results = {f: ("breaks" if per_file[f] else group, per_file[f][0][0] if per_file[f] else "")
               for f in files}
    record_receipts(repo, results, checks, after, useful)
    filled = fill_verdicts(repo, results, useful)
    if broken:
        print("DELETE-CHECK: breaks(" + "; ".join(label for label, _ in broken) + "): "
              + ("each file's own result above is recorded; the ok ones count as tried alone"
                 if len(files) > 1 else "keep it, it is live"))
        print_filled(filled)
        return 1
    if not useful:
        print("DELETE-CHECK: unchecked(every check was already failing)")
        return 2
    if all(label.startswith("tests:") for label in useful):
        print_filled(filled)
        print("DELETE-CHECK: weak(tests only): unit tests notice only what they call. Find what reaches "
              "this code (its loader, a schedule, a config entry, the app's commands) and rerun with "
              "--run \"<that command>\" for each.")
        return 2
    print_filled(filled)
    print("DELETE-CHECK: nothing-breaks(" + "; ".join(useful) + ")")
    return 0


# ---------------- gates: what a finished cleanup must show -------------------
LEDGER = ".latent"
VERDICTS = LEDGER + "/verdicts.md"
RECEIPTS = LEDGER + "/receipts.json"
INVENTORY = LEDGER + "/inventory.json"
SNAPSHOT = LEDGER + "/snapshot.json"
LOADER_NOTE = re.compile(r"^\s*[-*]\s+loader\s+`?([^`\s]+:\d+)`?\s*:\s*(.*\S)\s*$", re.I)
VERDICT = re.compile(r"^\s*[-*]\s+`?([^`\s:]+)`?\s*:\s*(dead|live|watch)\s*:\s*(.*\S)\s*$", re.I)
CITE = re.compile(r"`?([\w./\\-]+\.[A-Za-z]\w*):(\d+)`?")


def file_sha(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()
    except OSError:
        return None


def read_json(repo, rel_path, default):
    try:
        with open(os.path.join(repo, rel_path), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_json(repo, rel_path, data):
    os.makedirs(os.path.join(repo, LEDGER), exist_ok=True)
    with open(os.path.join(repo, rel_path), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
        fh.write("\n")


def code_files(repo):
    return sorted(rel_to(p, repo) for p in iter_files([repo], PY_EXT)
                  if not rel_to(p, repo).startswith(LEDGER + "/"))


def ensure_inventory(repo):
    """The code as it was before the cleanup started, so the gate can see what was deleted."""
    inv = read_json(repo, INVENTORY, None)
    if inv is None:
        inv = {f: file_sha(os.path.join(repo, f)) for f in code_files(repo)}
        write_json(repo, INVENTORY, inv)
    return inv


def record_receipts(repo, results, checks, after, useful):
    """Keep one receipt per file: what deleting it did, against which checks, and those checks'
    output after the deletion, so the gate can rerun them once the file is really gone."""
    receipts = read_json(repo, RECEIPTS, {})
    for f, (verdict, broke) in results.items():
        receipts[f.replace("\\", "/")] = {
            "result": verdict, "broke": broke, "sha": file_sha(os.path.join(repo, f)),
            "checks": [[label, cmd, shell] for label, cmd, shell in checks if label in useful],
            "after": {label: [after[label][0], after[label][1]] for label in useful}}
    write_json(repo, RECEIPTS, receipts)


def current_suspects(repo):
    """(suspect files, mapped files no import names) for the repo as it is now."""
    pyfiles = [p for p in iter_files([repo], PY_EXT) if not rel_to(p, repo).startswith(LEDGER + "/")]
    modules, edges, _asts = build_graph(pyfiles, [repo])
    mapped = mapped_files(repo)
    dead = check_dead_modules(modules, edges, [repo], set(), mapped, repo, rescue=False)
    imported = {dst for targets in edges.values() for dst, _ in targets}
    # code imported only by suspects goes when they go: a suspect too, found now, not a round later
    suspect_mods = {m for m, p in modules.items() if any(d["file"] == p for d in dead)}
    importers = defaultdict(set)
    for src, targets in edges.items():
        for dst, _ln in targets:
            importers[dst].add(src)
    grew = True
    while grew:
        grew = False
        for m, p in modules.items():
            if m in suspect_mods or rel_to(p, repo) in mapped or m.split(".")[-1] in ENTRY_BASENAMES                     or m.split(".")[-1].startswith("test"):
                continue
            if importers[m] and importers[m] <= suspect_mods:
                suspect_mods.add(m)
                dead.append({"module": m, "file": p})
                grew = True
    entry = mapped_entry_files(repo)
    looks_dead = sorted(rel_to(p, repo) for m, p in modules.items()
                        if rel_to(p, repo) in mapped and rel_to(p, repo) not in entry
                        and m not in imported and m.split(".")[-1] not in ENTRY_BASENAMES)
    return sorted(rel_to(d["file"], repo) for d in dead), looks_dead, mapped


VERDICTS_HEAD = ("# Verdicts\n\nOne line per suspect: `- <file>: dead|live|watch: <why>`. A live one cites the\n"
                 "`file:line` that reaches it. Lines a try-delete proved are written for you; edit the why freely.\n\n")


def fill_verdicts(repo, results, useful):
    """Write the verdict a receipt proves for each file that has none yet (or only a draft slot):
    `breaks` is live, `nothing-breaks` is dead. A verdict already written is never changed."""
    path = os.path.join(repo, VERDICTS)
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        lines = VERDICTS_HEAD.rstrip("\n").splitlines() + [""]
    have, _slots = read_verdicts(repo)
    filled = []
    for f, (result, broke) in results.items():
        f = f.replace("\\", "/")
        if f in have or result not in ("breaks", "nothing-breaks"):
            continue
        line = (f"- {f}: live: deleting it breaks {broke}" if result == "breaks" else
                f"- {f}: dead: deleting it broke none of: {'; '.join(useful)}")
        slot = next((i for i, x in enumerate(lines) if "[[fill" in x and re.match(
            r"^\s*[-*]\s+`?" + re.escape(f) + r"`?\s*:", x)), None)
        if slot is None:
            lines.append(line)
        else:
            lines[slot] = line
        filled.append(f)
    if filled:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
    return filled


def print_filled(filled):
    if filled:
        print(f"Wrote {len(filled)} proven verdict(s) to {VERDICTS}; next: H --gate")


def read_verdicts(repo):
    """{file: (verdict, reason)} from .latent/verdicts.md, plus the lines left as a draft slot."""
    out, unfilled = {}, []
    try:
        with open(os.path.join(repo, VERDICTS), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return out, unfilled
    for line in lines:
        if "[[fill" in line:
            m = re.match(r"^\s*[-*]\s+`?([^`\s:]+)", line)
            if m:
                unfilled.append(m.group(1))
            continue
        m = VERDICT.match(line)
        if m:
            out[m.group(1).replace("\\", "/")] = (m.group(2).lower(), m.group(3).strip())
    return out, unfilled


def name_parts(rel_path):
    stem = os.path.splitext(os.path.basename(rel_path))[0]
    return stem, {x for x in re.split(r"[_\-.]", stem) if len(x) >= 2}


def fragments(rel_path, others=()):
    """The suspect's name as a schedule, format list or config could spell it. A part shared with
    another suspect (`report` in every `*_report`) is not a name, so it does not count."""
    stem, parts = name_parts(rel_path)
    common = set()
    for o in others:
        if o != rel_path:
            common |= name_parts(o)[1]
    return {stem, stem.replace("_", "-")} | (parts - common)


def citation_problem(repo, suspect, reason, others=()):
    """None when the reason cites a real line, outside the suspect, that names it or part of its name."""
    cites = CITE.findall(reason)
    if not cites:
        return "cites no `file:line` that reaches it"
    names = fragments(suspect, others)
    for path, line in cites:
        path = path.replace("\\", "/")
        full = os.path.join(repo, path)
        if path == suspect or not os.path.isfile(full):
            continue
        with open(full, encoding="utf-8", errors="replace") as fh:
            text = fh.read().splitlines()
        n = int(line)
        if 1 <= n <= len(text) and any(re.search(r"(?<![A-Za-z0-9])" + re.escape(x) + r"(?![A-Za-z0-9])",
                                                 text[n - 1]) for x in names):
            return None
    return ("no cited line names it: point at the line holding its name or part of it "
            f"({', '.join(sorted(names))}), e.g. the schedule entry or the format list")


def dynamic_loaders(repo):
    """[(module prefix, "file:line")] for each import whose module name is built at runtime:
    `import_module(f"{__name__}.{fmt}_report")` loads from this package, `"jobs." + name` from jobs."""
    out = []
    for path in iter_files([repo], PY_EXT):
        tree = parse_tree(path)
        if tree is None:
            continue
        here = module_name(path, [repo])
        here = here[:-len(".__init__")] if here.endswith(".__init__") else here
        for n in ast.walk(tree):
            if not (isinstance(n, ast.Call) and n.args):
                continue
            fn = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
            arg = n.args[0]
            if fn not in ("import_module", "__import__") or isinstance(arg, ast.Constant):
                continue
            prefix = ""
            if isinstance(arg, ast.JoinedStr):
                for part in arg.values:
                    if isinstance(part, ast.Constant):
                        prefix += str(part.value)
                    elif isinstance(part, ast.FormattedValue) and not prefix                             and getattr(part.value, "id", "") == "__name__":
                        prefix = here
                    else:
                        break
            elif isinstance(arg, ast.BinOp) and isinstance(arg.left, ast.Constant):
                prefix = str(arg.left.value)
            if prefix:
                out.append((prefix, f"{rel_to(path, repo)}:{n.lineno}"))
    return out


def loaded_by(repo, suspect, loaders):
    """The first loader that can build this suspect's module name, or None."""
    mod = os.path.splitext(suspect)[0].replace("/", ".")
    return next((where for prefix, where in loaders if mod.startswith(prefix)), None)


def name_mention(repo, suspect, skip):
    """The first `file:line` outside the suspect (and outside files in `skip`) that spells its
    name as a whole word, `rollup_daily` or `rollup-daily`: a schedule, a config, a format list."""
    stem = os.path.splitext(os.path.basename(suspect))[0]
    pat = re.compile(r"(?<![A-Za-z0-9_-])(" + re.escape(stem) + "|" + re.escape(stem.replace("_", "-"))
                     + r")(?![A-Za-z0-9_-])")
    for path in iter_files([repo], TEXT_EXT):
        rel_path = rel_to(path, repo)
        if rel_path == suspect or rel_path in skip or rel_path.startswith(".features/"):
            continue
        in_code = rel_path.endswith(".py")  # imports are the graph's job: in code, only strings count
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                for n, line in enumerate(fh, 1):
                    m = pat.search(line)
                    if m and (not in_code or re.search(r"[\"'][^\"']*" + re.escape(m.group(1)), line)):
                        return f"{rel_path}:{n}"
        except OSError:
            continue
    return None


def print_leads(repo, suspects, loaders):
    """Before any try-delete: what could reach the suspects, found mechanically, so the agent knows
    which commands to --run without reading every module."""
    by_loader, by_mention = defaultdict(list), defaultdict(list)
    for f in suspects:
        loader = loaded_by(repo, f, loaders)
        if loader:
            by_loader[loader].append(f)
        where = name_mention(repo, f, set(suspects))
        if where:
            by_mention[where.rsplit(":", 1)[0]].append(f)
    if not (by_loader or by_mention):
        return
    print("LEADS: what could reach the suspects. --run the commands that call these:")
    for where, fs in sorted(by_loader.items()):
        path, line = where.rsplit(":", 1)
        with open(os.path.join(repo, path), encoding="utf-8", errors="replace") as fh:
            text = fh.read().splitlines()[int(line) - 1].strip()
        print(f"  {where} builds module names at runtime: {text[:100]}  ({len(fs)} suspects in its package)")
    for path, fs in sorted(by_mention.items()):
        print(f"  {path} spells {len(fs)} suspect name(s): {', '.join(os.path.basename(x) for x in fs[:6])}"
              + (" ..." if len(fs) > 6 else ""))
    print()


def take_snapshot(repo, runs):
    """Stage 1: run every command that could load code (plus the map's runs, VERIFY.md and the unit
    tests) in a copy, recording what each one imported. Refused once code has been deleted."""
    inventory = ensure_inventory(repo)
    deleted = [f for f in inventory if not os.path.exists(os.path.join(repo, f))]
    if deleted:
        print(f"SNAPSHOT: refused: {len(deleted)} file(s) already deleted ({', '.join(deleted[:3])}). "
              "A snapshot is the before picture: restore them first.")
        return 2
    checks = recorded_checks(repo, list(runs))
    imports = {}
    results = run_checks(repo, checks, imports=imports)
    suspects = current_suspects(repo)[0]
    loaded = {}
    for label in imports:
        for f in imports[label]:
            loaded.setdefault(f, label)
    write_json(repo, SNAPSHOT, {
        "checks": [[label, cmd, shell] for label, cmd, shell in checks],
        "results": {label: [results[label][0], results[label][1]] for label in results},
        "loaded": loaded, "suspects": suspects,
        "shas": {f: file_sha(os.path.join(repo, f)) for f in code_files(repo)}})
    live = [f for f in suspects if f in loaded]
    print(f"SNAPSHOT: {len(checks)} command(s); {len(live)} of {len(suspects)} suspects loaded (live), "
          f"{len(suspects) - len(live)} never loaded. Failing before any change: "
          + (", ".join(label for label in results if results[label][0] != 0) or "none"))
    print("next: H --gate")
    return 0


def gate(repo, runs=()):
    """Check the three stages; print every problem at once, with its fix. 0 done, 1 open.
    With --run, take the snapshot first (stage 1)."""
    if runs and not os.path.isfile(os.path.join(repo, SNAPSHOT)):
        if take_snapshot(repo, runs) == 2:
            return 1
        print()
    inventory = ensure_inventory(repo)
    receipts = read_json(repo, RECEIPTS, {})
    snap = read_json(repo, SNAPSHOT, None)
    loaders = dynamic_loaders(repo)
    verdicts, unfilled = read_verdicts(repo)
    notes = {}
    try:
        with open(os.path.join(repo, VERDICTS), encoding="utf-8") as fh:
            for line in fh:
                m = LOADER_NOTE.match(line)
                if m:
                    notes[m.group(1).replace("\\", "/")] = m.group(2)
    except OSError:
        pass
    deleted = sorted(f for f in inventory if not os.path.exists(os.path.join(repo, f)))
    problems = {1: [], 2: [], 3: []}
    print('H = python "' + os.path.abspath(__file__) + '" ' + repo)

    # stage 1: a snapshot exists, is current, and exercised every runtime loader
    if snap is None:
        suspects = current_suspects(repo)[0]
        print_leads(repo, suspects, loaders)
        problems[1].append('no snapshot. Run every command that could load code, before changing anything: '
                           'H --snapshot --run "<cmd>" --run "<cmd>" ... (each CLI command, each format, '
                           'the job runner; the map, VERIFY.md and unit tests are added for you)')
        loaded, suspects = {}, suspects
    else:
        loaded, suspects = snap["loaded"], snap["suspects"]
        changed = [f for f, sha in snap["shas"].items()
                   if os.path.exists(os.path.join(repo, f)) and file_sha(os.path.join(repo, f)) != sha]
        if changed:
            problems[1].append(f"changed since the snapshot: {', '.join(changed[:5])}. Delete only; after "
                               "other edits, restore any deleted files and rerun H --snapshot")
        for prefix, where in loaders:
            mine = [f for f in suspects if os.path.splitext(f)[0].replace("/", ".").startswith(prefix)]
            if mine and not any(f in loaded for f in mine) and where not in notes:
                problems[1].append(
                    f"{where} builds module names at runtime, but no snapshot command made it load any of "
                    f"its {len(mine)} suspects. Rerun H --snapshot with the commands that call it added, "
                    f"or add `- loader {where}: <why it loads none>` to {VERDICTS}")

    # stage 2: deletions only of what the snapshot never loaded, and nothing that ran breaks now
    dead_files = {x for x, (vv, _rr) in verdicts.items() if vv == "dead"}
    for f in deleted:
        r = receipts.get(f) or {}
        if f in loaded:
            problems[2].append(f"{f}: deleted, but the snapshot saw it loaded by {loaded[f]}. Restore it")
        elif f not in suspects and r.get("result") != "nothing-breaks":
            problems[2].append(f"{f}: deleted, but it was not a suspect the snapshot covered. Restore it, or "
                               f'prove it first: H --try-delete {f} --run "<cmd>"')
        else:
            where = name_mention(repo, f, set(deleted) | dead_files)
            if where and where not in verdicts.get(f, ("", ""))[1]:
                problems[2].append(f"{f}: deleted, but {where} spells its name. Add `- {f}: dead: <why "
                                   f"{where} never loads it>` to {VERDICTS}, or restore it")
    if deleted and snap:
        checks = [tuple(c) for c in snap["checks"]]
        now = run_checks(repo, checks)
        for label, _cmd, _sh in checks:
            new = new_problems(snap["results"][label], now[label])
            if new:
                problems[2].append(f"after the deletions, {label} fails: {new[-1][:160]}. Restore what it needs")

    # stage 3: every suspect still on disk is accounted for
    missing = []
    for f in suspects:
        if f in deleted or f in loaded or (receipts.get(f) or {}).get("result") == "breaks":
            continue
        v = verdicts.get(f)
        if v is None:
            missing.append(f)
        elif v[0] == "live" and citation_problem(repo, f, v[1], suspects):
            problems[3].append(f"{f}: kept as live, but the snapshot never loaded it and "
                               + citation_problem(repo, f, v[1], suspects))
        elif v[0] == "dead":
            where = name_mention(repo, f, dead_files)
            if where and where not in v[1]:
                problems[3].append(f"{f}: dead, but {where} spells its name: say why it never loads it")
    if snap is not None and missing and not problems[1]:
        path = os.path.join(repo, VERDICTS)
        lines = []
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        new = [f for f in missing if f not in unfilled]
        if new:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(lines or VERDICTS_HEAD.rstrip("\n").splitlines() + [""]) + "\n"
                         + "".join(f"- {f}: [[fill: dead | watch | live]]: [[fill: why]]\n" for f in new))
        problems[3].append(f"{len(missing)} suspect(s) the snapshot never loaded are still here, with no "
                           f"verdict: delete them, or fill their slot in {VERDICTS} (dead to report "
                           f"without deleting, watch to keep, live with the file:line that loads it): "
                           + ", ".join(missing[:8]) + (" ..." if len(missing) > 8 else ""))

    names = {1: "snapshot: every loader exercised", 2: "change: only never-loaded code deleted, nothing broke",
             3: "account: every suspect left has a verdict"}
    for g in (1, 2, 3):
        print(f"STAGE {g} {names[g]}: " + ("holds" if not problems[g] else f"open, {len(problems[g])} to fix"))
        for line in problems[g]:
            print(f"  - {line}")
    open_stages = [g for g in (1, 2, 3) if problems[g]]
    if open_stages:
        print(f"LATENT-GATE: open({', '.join(str(g) for g in open_stages)}): fix the lines above, then H --gate")
        return 1

    removed = list(deleted)
    live = [(f, f"loaded by {loaded[f]}") for f in suspects if f in loaded]
    live += [(f, f"deleting it breaks {receipts[f]['broke']}") for f in suspects
             if f not in loaded and (receipts.get(f) or {}).get("result") == "breaks"]
    live += [(f, r) for f, (v, r) in sorted(verdicts.items()) if v == "live" and f not in dict(live)]
    dead_kept = [(f, r) for f, (v, r) in sorted(verdicts.items()) if v == "dead" and f not in deleted]
    watch = [(f, r) for f, (v, r) in sorted(verdicts.items()) if v == "watch" and f not in deleted]
    print("ANSWER (drafted from the ledger; give it, adding only context):\n")
    if removed:
        print(f"Removed ({len(removed)}; the snapshot never loaded them, and every command still passes):")
        print("".join(f"- {f}" + (f": {verdicts[f][1]}" if f in verdicts else "") + "\n" for f in removed), end="")
    if live:
        print(f"Kept, though no import names them ({len(live)}):")
        print("".join(f"- {f}: {r}\n" for f, r in live), end="")
    if dead_kept:
        print("Dead, not deleted:")
        print("".join(f"- {f}: {r}\n" for f, r in dead_kept), end="")
    if watch:
        print("Watch:")
        print("".join(f"- {f}: {r}\n" for f, r in watch), end="")
    print(f"\nLATENT-GATE: done({len(removed)} removed, {len(live)} live, {len(dead_kept)} dead not removed, "
          f"{len(watch)} watch)")
    return 0


# ---------------- report -----------------------------------------------------
def rel(p):
    try:
        return os.path.relpath(p)
    except ValueError:
        return p


def latent_verdict(n_modules, dead, unused, breaches, layers_measured):
    """The LATENT summary line.

    With no --layers file the layer dimension was not measured at all, so `layer-breaches: 0`
    would claim a clean result for ground never walked. Report it as UNMEASURED instead.
    """
    if not layers_measured:
        layer_count = "UNMEASURED(no --layers declared)"
    else:
        layer_count = str(len(breaches))
    if dead or unused or breaches:
        return (f"LATENT: findings(dead: {len(dead)}, unused: {len(unused)}, "
                f"layer-breaches: {layer_count})")
    if layers_measured:
        return f"LATENT: clean({n_modules} modules traced)"
    return f"LATENT: findings(dead: 0, unused: 0, layer-breaches: {layer_count})"


def main():
    utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--layers", help="declared layer order file")
    ap.add_argument("--entry", action="append", default=[],
                    help="module known to be an entry point (repeatable)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--edges", help="also write the import graph to this JSON file")
    ap.add_argument("--try-delete", nargs="+", metavar="FILE",
                    help="delete these (paths from the repo root) in a throwaway copy and report what breaks")
    ap.add_argument("--snapshot", action="store_true",
                    help="stage 1: run the --run commands in a copy and record what each one imported")
    ap.add_argument("--gate", action="store_true",
                    help="check the cleanup's four gates from .latent/ and draft the answer")
    ap.add_argument("--run", action="append", default=[], metavar="CMD",
                    help="with --try-delete or --gate: a command that reaches the code, run before and after "
                         "(repeatable)")
    args = ap.parse_args()

    repo = args.paths[0] if os.path.isdir(args.paths[0]) else (os.path.dirname(args.paths[0]) or ".")
    if args.try_delete:
        return try_delete(repo, args.try_delete, args.run)
    if args.snapshot:
        return take_snapshot(repo, args.run)
    if args.gate:
        return gate(repo, args.run)

    pyfiles = [p for p in iter_files(args.paths, PY_EXT)]
    if not pyfiles:
        print("LATENT: blocked(no analyzable source)")
        return 2

    modules, edges, asts = build_graph(pyfiles, args.paths)
    if args.edges:
        with open(args.edges, "w", encoding="utf-8") as f:
            json.dump({"modules": {m: os.path.abspath(p) for m, p in modules.items()},
                       "edges": [{"from": a, "to": b, "line": ln}
                                 for a in sorted(edges) for b, ln in sorted(edges[a])]},
                      f, indent=1)
    mapped = mapped_files(repo)
    dead = check_dead_modules(modules, edges, args.paths, set(args.entry), mapped, repo)
    imported = {dst for targets in edges.values() for dst, _ in targets}
    entry_files = mapped_entry_files(repo)
    mapped_mods = sorted((rel_to(p, repo), mapped[rel_to(p, repo)],
                          m not in imported and m.split(".")[-1] not in ENTRY_BASENAMES
                          and rel_to(p, repo) not in entry_files)
                         for m, p in modules.items() if rel_to(p, repo) in mapped)
    unused = check_unused_defs(modules, asts, args.paths)
    breaches, unmapped, layers = [], [], None
    if args.layers:
        layers = load_layers(args.layers)
        breaches, unmapped = check_layers(modules, edges, layers)

    result = {"modules": len(modules),
              "edges": sum(len(v) for v in edges.values()),
              "layer_breaches": breaches, "layer_unmapped": unmapped,
              "dead_modules": dead, "unused_defs": unused,
              "layers_declared": bool(args.layers),
              "mapped": [{"file": f, "feature": n, "no_importer": x} for f, n, x in mapped_mods]}

    n_findings = len(breaches) + len(dead) + len(unused)
    result["verdict"] = latent_verdict(len(modules), dead, unused, breaches,
                                       layers_measured=bool(args.layers))
    result["layers_measured"] = bool(args.layers)

    if args.json:
        print(json.dumps(result, indent=2))
        return 1 if n_findings else 0
    else:
        print(f"GRAPH — {result['modules']} modules, "
              f"{result['edges']} import edges traced.")
        print()
        if args.layers:
            names = " > ".join(n for n, _ in layers)
            if breaches:
                print(f"LAYER BREACHES (proven) — declared order: {names}")
                for b in breaches:
                    print(f"  {rel(b['file'])}:{b['line']}  {b['edge']}")
                    print(f"      breaks: {b['rule']}")
            else:
                print(f"LAYERS (proven) — clean against declared "
                      f"order: {names}")
            if unmapped:
                print(f"  note: {len(unmapped)} modules match no declared "
                      f"layer (spec incomplete, not a breach): "
                      + ", ".join(unmapped[:8])
                      + (" …" if len(unmapped) > 8 else ""))
        else:
            print("LAYERS — not checked: no --layers file declared. "
                  "This is a gap, not a clean result.")
        print()
        if mapped_mods:
            print(f"MAPPED (live) - FEATURES.md names these {len(mapped_mods)} files, so they are "
                  "never candidates:")
            for f, n, x in mapped_mods:
                print(f"  {f}  ({n})" + ("  no import names it: kept, though it looks dead" if x else ""))
            print()
        if dead:
            print("DEAD MODULE CANDIDATES (suspected) — nothing in-tree "
                  "imports or textually references these:")
            for d in dead:
                print(f"  {d['module']}  ({rel(d['file'])})")
        else:
            print("DEAD MODULES (suspected sweep) — none found.")
        print()
        if unused:
            print("UNUSED DEFS (suspected) — defined, never referenced "
                  "in-tree (dunder/test/decorated excluded):")
            for u in unused:
                print(f"  {u['name']}  ({rel(u['file'])}:{u['line']})")
        else:
            print("UNUSED DEFS (suspected sweep) — none found.")
        print()
        print("WARNING — (suspected) means statically unreferenced, NOT "
              "provably dead: dynamic dispatch, reflection, external "
              "callers, and plugins are invisible here. Per latent-audit, "
              "NOTHING may be deleted from this report alone: run "
              "--try-delete on it first.")
        print()

    print(result["verdict"])
    return 1 if n_findings else 0  # unmeasured ≠ defect; see `latent_verdict` and the docstring


if __name__ == "__main__":
    sys.exit(main())
