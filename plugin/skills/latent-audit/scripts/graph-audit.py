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

Usage:
  python3 scripts/graph-audit.py <path> [<path> ...]
        [--layers LAYERS_FILE] [--entry MODULE ...] [--json] [--edges FILE]
  python3 scripts/graph-audit.py <repo> --try-delete FILE [FILE ...] [--run CMD ...]

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
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist",
             "build", ".tox", ".mypy_cache", ".pytest_cache"}

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
def check_dead_modules(modules, edges, roots, declared_entries, mapped=None, repo="."):
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


def run_checks(repo, checks, delete=()):
    """{label: (exit code, problem lines)} for every check, run in a throwaway copy of repo with
    `delete` removed, so the repo itself is never touched. Problem lines are the output lines that
    name a failure, with the copy's path removed, so two runs can be compared line by line."""
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
        for label, cmd, shell in checks:
            try:
                p = subprocess.run(cmd, cwd=copy, shell=shell, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=300, env=env)
                text = ((p.stdout or "") + (p.stderr or "")).replace(copy, "<repo>")
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()] or [""]
                out[label] = (p.returncode, [ln for ln in lines if PROBLEM.search(ln)] or lines[-1:])
            except subprocess.TimeoutExpired:
                out[label] = ("timeout", ["timed out"])
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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
    before = run_checks(repo, checks)
    after = run_checks(repo, checks, files)
    print(f"DELETE-CHECK of {len(files)} file(s), each check run before and after in a throwaway copy:")
    for label in after:
        why = new_problems(before[label], after[label])
        state = ("BREAKS" if why else "still passes" if after[label][0] == 0 else
                 "already failing, nothing new")
        print(f"  {state:<29} {label}" + (f"  ({why[-1][:160]})" if why else ""))
    broken = broken_by(before, after)
    if broken and len(files) > 1:
        print("Which file breaks it, each deleted alone:")
        for f in files:
            alone = broken_by(before, run_checks(repo, checks, [f]))
            print(f"  {'LIVE' if alone else 'ok':<5} {f}" + (f"  breaks: {alone[0][0]}" if alone else ""))
    useful = [label for label in before if before[label][0] == 0 or label.startswith("map:")]
    if broken:
        print("DELETE-CHECK: breaks(" + "; ".join(label for label, _ in broken) + "): "
              + ("keep each LIVE file above; try-delete the ok ones again on their own"
                 if len(files) > 1 else "keep it, it is live"))
        return 1
    if not useful:
        print("DELETE-CHECK: unchecked(every check was already failing)")
        return 2
    if all(label.startswith("tests:") for label in useful):
        print("DELETE-CHECK: weak(tests only): unit tests notice only what they call. Find what reaches "
              "this code (its loader, a schedule, a config entry, the app's commands) and rerun with "
              "--run \"<that command>\" for each.")
        return 2
    print("DELETE-CHECK: nothing-breaks(" + "; ".join(useful) + ")")
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
    ap.add_argument("--run", action="append", default=[], metavar="CMD",
                    help="with --try-delete: a command that reaches the code, run before and after (repeatable)")
    args = ap.parse_args()

    repo = args.paths[0] if os.path.isdir(args.paths[0]) else (os.path.dirname(args.paths[0]) or ".")
    if args.try_delete:
        return try_delete(repo, args.try_delete, args.run)

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
