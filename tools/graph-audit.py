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

Stdlib only, mirroring tools/structure-report.py.  Python-deep; the report
says exactly where depth stops rather than dressing shallow up as uniform.

Usage:
  python3 tools/graph-audit.py <path> [<path> ...]
        [--layers LAYERS_FILE] [--entry MODULE ...] [--json]

Layers file format (top layer first; a module may import SAME or LOWER
layers, never a HIGHER one), '#' comments allowed:

    interface: app/routes/, app/cli/
    domain:    app/services/
    data:      app/models/, app/db/

Verdict line (noun owned by the latent-audit skill; grammar per PROTOCOL.md):
  LATENT: clean(N modules traced)
        | findings(dead: A, unused: B, layer-breaches: C)
        | blocked(no analyzable source)
"""

import argparse
import ast
import json
import os
import sys
from collections import defaultdict

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


# ---------------- check 2: dead modules (suspected) --------------------------
def check_dead_modules(modules, edges, roots, declared_entries):
    imported = {dst for targets in edges.values() for dst, _ in targets}
    candidates = []
    for mod, path in modules.items():
        base = mod.split(".")[-1]
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


# ---------------- report -----------------------------------------------------
def rel(p):
    try:
        return os.path.relpath(p)
    except ValueError:
        return p


def main():
    # ponytail: real portability bug, one guarded line; no-op where stdout is already UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--layers", help="declared layer order file")
    ap.add_argument("--entry", action="append", default=[],
                    help="module known to be an entry point (repeatable)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    pyfiles = [p for p in iter_files(args.paths, PY_EXT)]
    if not pyfiles:
        print("LATENT: blocked(no analyzable source)")
        return 2

    modules, edges, asts = build_graph(pyfiles, args.paths)
    dead = check_dead_modules(modules, edges, args.paths, set(args.entry))
    unused = check_unused_defs(modules, asts, args.paths)
    breaches, unmapped, layers = [], [], None
    if args.layers:
        layers = load_layers(args.layers)
        breaches, unmapped = check_layers(modules, edges, layers)

    result = {"modules": len(modules),
              "edges": sum(len(v) for v in edges.values()),
              "layer_breaches": breaches, "layer_unmapped": unmapped,
              "dead_modules": dead, "unused_defs": unused,
              "layers_declared": bool(args.layers)}

    n_findings = len(breaches) + len(dead) + len(unused)
    verdict = (f"LATENT: findings(dead: {len(dead)}, unused: {len(unused)}, "
               f"layer-breaches: {len(breaches)})" if n_findings
               else f"LATENT: clean({len(modules)} modules traced)")
    result["verdict"] = verdict

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
              "NOTHING may be deleted from this report alone; every "
              "candidate needs a disconnection proof first.")
        print()

    print(verdict)
    return 1 if n_findings else 0


if __name__ == "__main__":
    sys.exit(main())
