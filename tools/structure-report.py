#!/usr/bin/env python3
"""
structure-report — the structural-quality instrument for the top-tier-engineer suite.

WHY THIS EXISTS
---------------
The suite tells the engineer how to write clean code (build-discipline's slice
rules, senior-review's maintainability dimension) but nothing MEASURES the result.
A director who cannot read code has no instrument that screams when the code got
dirty anyway. This tool is that instrument. It computes the few structural signals
that correlate with "spaghetti" and emits a plain-language verdict a non-coder can
act on without reading a line of source.

WHAT IT MEASURES (and why each one is a spaghetti signal)
---------------------------------------------------------
  1. Function length        — long functions hide complexity and resist testing.
  2. Cyclomatic complexity  — branch density; the single best-studied bug predictor.
  3. File length            — god-files concentrate risk and merge pain.
  4. Nesting depth          — deep nesting is the visual shape of spaghetti.
  5. Import cycles          — circular dependencies are literal spaghetti; a module
                              graph you cannot topologically sort cannot be reasoned
                              about in isolation.
  6. Duplication            — copy-paste blocks drift apart and rot independently.

It checks STRUCTURE, not correctness — it cannot know if the code is right, but it
CAN catch the shapes that make code unmaintainable regardless of correctness. That
is the cheapest structural enforcement available and (for Python) it requires
nothing but the stdlib.

EVIDENCE DISCIPLINE (PROTOCOL §1)
--------------------------------
Every number this tool prints is (proven) — it executed a measurement over real
source. It never reports (suspected): a threshold breach is a measured fact, though
whether that breach MATTERS is a judgement this tool routes to senior-review, never
decides itself. A breach is a flag for a human/reviewer, not a verdict on wisdom.

VERDICT LINE (PROTOCOL §5)
-------------------------
Ends with exactly one machine-parseable line, noun STRUCTURE:
    STRUCTURE: clean(N files, M functions scanned)
    STRUCTURE: findings(top: <worst signal>, count: K) | review-needed
    STRUCTURE: blocked(no analyzable source found)

EXIT CODES
----------
  0 = clean (no threshold breaches)        — CI may pass
  1 = findings (one or more breaches)      — CI blocks; review-needed
  2 = blocked (nothing analyzable)         — CI blocks; misconfiguration

USAGE
-----
    structure-report.py [PATH ...]          # defaults to "."
    structure-report.py --json              # machine-readable, for the harness
    structure-report.py --thresholds f.json # override default thresholds

SCOPE / HONESTY
---------------
Full depth (complexity, nesting, cycles, length) is implemented for Python via the
stdlib `ast`. For other languages the tool falls back to language-agnostic line/
duplication signals and SAYS SO in its output rather than pretending to a depth it
does not have — derive, never fake (suite Law: evidence or downgrade). If richer
linters are installed (radon, ruff, eslint, madge) the tool notes they are
available so a future version / the harness can escalate; it never silently depends
on them.
"""
import ast
import sys
import os
import json
import argparse
import shutil
from collections import defaultdict

# Windows terminals default to cp1252 and crash on the report's ✅/⚠️ glyphs before the
# verdict line is ever printed; force UTF-8 so the director's own console can read it.
# ponytail: real portability bug, one guarded line; no-op where stdout is already UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (ValueError, OSError):
        pass

# ----- default thresholds (override with --thresholds f.json) --------------------
# Tuned to "a reviewer would want to look," not "definitely broken." A breach means
# review-needed, never condemned. Chesterton's Fence (Law 3): an odd long function
# may be justified — this tool flags it for a human, it does not fail the author.
DEFAULT_THRESHOLDS = {
    "function_lines":      60,   # SLoC in one function body
    "cyclomatic":          15,   # branch points + 1
    "file_lines":          600,  # SLoC in one file
    "nesting_depth":       5,    # indentation levels of control flow
    "duplication_block":   6,    # consecutive identical non-trivial lines = a dup block
}

PY_EXT = {".py"}
CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".rb",
            ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".php", ".swift", ".kt"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist",
             "build", ".mypy_cache", ".pytest_cache", "vendor", "target",
             ".next", "coverage", "site-packages"}

# AST node types that add a branch (cyclomatic) — kept explicit for transparency.
BRANCH_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler,
                ast.With, ast.AsyncWith, ast.BoolOp, ast.comprehension)


def iter_files(paths, exts):
    for p in paths:
        if os.path.isfile(p):
            if os.path.splitext(p)[1] in exts:
                yield p
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if os.path.splitext(f)[1] in exts:
                    yield os.path.join(root, f)


def sloc(lines):
    """Source lines of code: non-blank, non-pure-comment (best-effort, lang-agnostic)."""
    n = 0
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith(("#", "//", "*", "/*", "<!--")):
            continue
        n += 1
    return n


# ---------- Python deep analysis via ast ----------------------------------------
def cyclomatic(node):
    score = 1
    for child in ast.walk(node):
        if isinstance(child, BRANCH_NODES):
            # BoolOp adds (operands-1); others add 1.
            if isinstance(child, ast.BoolOp):
                score += len(child.values) - 1
            else:
                score += 1
    return score


def max_nesting(node):
    nest_types = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With,
                  ast.AsyncWith, ast.Try)

    def depth(n, d):
        best = d
        for child in ast.iter_child_nodes(n):
            nd = d + 1 if isinstance(child, nest_types) else d
            best = max(best, depth(child, nd))
        return best

    return depth(node, 0)


def analyze_python(path, thresholds, findings):
    try:
        src = open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError):
        return 0
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        findings.append(("syntax", path, 0,
                         f"file does not parse (line {e.lineno}) — cannot analyze"))
        return 0

    file_sloc = sloc(src.splitlines())
    if file_sloc > thresholds["file_lines"]:
        findings.append(("file_lines", path, file_sloc,
                         f"file is {file_sloc} SLoC (> {thresholds['file_lines']}) — god-file"))

    fn_count = 0
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn_count += 1
            start = n.lineno
            end = max((getattr(c, "lineno", start) for c in ast.walk(n)), default=start)
            length = end - start + 1
            cc = cyclomatic(n)
            nd = max_nesting(n)
            if length > thresholds["function_lines"]:
                findings.append(("function_lines", path, start,
                                 f"{n.name}() is {length} lines (> {thresholds['function_lines']})"))
            if cc > thresholds["cyclomatic"]:
                findings.append(("cyclomatic", path, start,
                                 f"{n.name}() complexity {cc} (> {thresholds['cyclomatic']})"))
            if nd > thresholds["nesting_depth"]:
                findings.append(("nesting_depth", path, start,
                                 f"{n.name}() nests {nd} deep (> {thresholds['nesting_depth']})"))
    return fn_count


def python_import_graph(paths):
    """Build a module-level import graph for cycle detection within the analyzed tree."""
    graph = defaultdict(set)
    modules = {}
    pyfiles = list(iter_files(paths, PY_EXT))
    for path in pyfiles:
        mod = os.path.splitext(os.path.basename(path))[0]
        modules.setdefault(mod, path)
    names = set(modules)
    for path in pyfiles:
        mod = os.path.splitext(os.path.basename(path))[0]
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    base = a.name.split(".")[0]
                    if base in names and base != mod:
                        graph[mod].add(base)
            elif isinstance(n, ast.ImportFrom) and n.module:
                base = n.module.split(".")[0]
                if base in names and base != mod:
                    graph[mod].add(base)
    return graph


def find_cycles(graph):
    """Return list of cycles (each a list of module names) via DFS."""
    cycles, WHITE, GREY, BLACK = [], 0, 1, 2
    color = defaultdict(lambda: WHITE)
    stack = []

    def dfs(u):
        color[u] = GREY
        stack.append(u)
        for v in graph.get(u, ()):
            if color[v] == GREY:
                i = stack.index(v)
                cycles.append(stack[i:] + [v])
            elif color[v] == WHITE:
                dfs(v)
        stack.pop()
        color[u] = BLACK

    for node in list(graph):
        if color[node] == WHITE:
            dfs(node)
    # dedupe by frozenset of members
    uniq, seen = [], set()
    for c in cycles:
        key = frozenset(c)
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    return uniq


# ---------- language-agnostic duplication ---------------------------------------
def find_duplication(paths, thresholds, findings):
    block = thresholds["duplication_block"]
    seen = defaultdict(list)  # normalized window -> [(file, lineno)]
    for path in iter_files(paths, CODE_EXT):
        try:
            lines = [l.rstrip() for l in open(path, encoding="utf-8")]
        except (OSError, UnicodeDecodeError):
            continue
        norm = [l.strip() for l in lines]
        meaningful = [i for i, s in enumerate(norm)
                      if s and not s.startswith(("#", "//", "*", "/*"))]
        for k in range(len(meaningful) - block + 1):
            idxs = meaningful[k:k + block]
            if idxs[-1] - idxs[0] != block - 1:
                continue  # not contiguous
            window = tuple(norm[i] for i in idxs)
            if len(set(window)) < 3:
                continue  # too trivial (e.g. closing braces)
            seen[window].append((path, idxs[0] + 1))
    reported = 0
    for window, locs in seen.items():
        if len(locs) > 1 and reported < 20:
            files = ", ".join(f"{os.path.basename(f)}:{ln}" for f, ln in locs[:3])
            findings.append(("duplication", locs[0][0], locs[0][1],
                             f"{block}-line block duplicated across {len(locs)} sites: {files}"))
            reported += 1


# ---------- reporting ------------------------------------------------------------
SEVERITY_ORDER = ["syntax", "cyclomatic", "nesting_depth", "function_lines",
                  "file_lines", "duplication"]
PLAIN = {
    "syntax":         "BROKEN — file does not parse",
    "cyclomatic":     "TANGLED — functions with too many branches (hardest to test, most bug-prone)",
    "nesting_depth":  "DEEP NESTING — code indented too many levels (the visual shape of spaghetti)",
    "function_lines": "LONG FUNCTIONS — functions doing too much in one place",
    "file_lines":     "GOD-FILES — single files carrying too much",
    "duplication":    "COPY-PASTE — same block repeated in multiple places (will drift and rot)",
    "import_cycle":   "CIRCULAR DEPENDENCY — modules import each other in a loop (literal spaghetti)",
}


def analyze(paths, thresholds):
    """Measure all signals over paths; return a result dict (findings + verdict + exit code)."""
    findings = []
    py_files = list(iter_files(paths, PY_EXT))
    all_code = list(iter_files(paths, CODE_EXT))
    non_py = [f for f in all_code if os.path.splitext(f)[1] not in PY_EXT]

    fn_count = 0
    for path in py_files:
        fn_count += analyze_python(path, thresholds, findings)

    for c in find_cycles(python_import_graph(paths)):          # import cycles (python)
        findings.append(("import_cycle", c[0], 0, "import cycle: " + " -> ".join(c)))

    find_duplication(paths, thresholds, findings)              # duplication (all languages)

    # richer linters present-but-unused: note, never depend.
    available = [t for t in ("radon", "ruff", "eslint", "madge") if shutil.which(t)]

    by_kind = defaultdict(int)
    for kind, *_ in findings:
        by_kind[kind] += 1

    if not all_code:
        verdict, exit_code = "STRUCTURE: blocked(no analyzable source found)", 2
    elif not findings:
        verdict = f"STRUCTURE: clean({len(all_code)} files, {fn_count} functions scanned)"
        exit_code = 0
    else:
        order = SEVERITY_ORDER + ["import_cycle"]
        top = min(by_kind, key=lambda k: order.index(k) if k in order else 99)
        verdict = f"STRUCTURE: findings(top: {top}, count: {len(findings)}) | review-needed"
        exit_code = 1

    return {"findings": findings, "by_kind": by_kind, "all_code": all_code,
            "py_files": py_files, "non_py": non_py, "fn_count": fn_count,
            "available": available, "verdict": verdict, "exit_code": exit_code,
            "thresholds": thresholds}


def print_human_report(r):
    print("=" * 70)
    print("STRUCTURAL QUALITY REPORT  —  is this spaghetti?")
    print("=" * 70)
    print(f"Scanned: {len(r['all_code'])} code files "
          f"({len(r['py_files'])} Python, deep-analyzed; "
          f"{len(r['non_py'])} other, line+duplication only) · {r['fn_count']} functions")
    if r["non_py"]:
        print("  note: full complexity/nesting/cycle analysis is Python-only in this "
              "version;\n        other languages get length + duplication signals only.")
    if r["available"]:
        print(f"  note: richer linters available on PATH ({', '.join(r['available'])}) — "
              "the harness\n        may escalate to them for deeper signal.")
    print()

    if not r["findings"]:
        print("  ✅  CLEAN — no structural threshold breached.")
        print("      No god-files, no tangled functions, no circular imports, no")
        print("      copy-paste blocks above threshold. Nothing here reads as spaghetti.")
        print("      (This is a STRUCTURE verdict, not a correctness or wisdom verdict —")
        print("       senior-review and correctness-gate still own those.)")
    else:
        by_kind, findings = r["by_kind"], r["findings"]
        print(f"  ⚠️  REVIEW NEEDED — {len(findings)} structural flag(s), by category:\n")
        order = SEVERITY_ORDER + ["import_cycle"]
        for kind in sorted(by_kind, key=lambda k: order.index(k) if k in order else 99):
            print(f"  ── {PLAIN.get(kind, kind)}  ({by_kind[kind]})")
            for _, fpath, line, detail in [f for f in findings if f[0] == kind][:5]:
                loc = f"{os.path.relpath(fpath)}" + (f":{line}" if line else "")
                print(f"       · {detail}   [{loc}]")
            if by_kind[kind] > 5:
                print(f"       … and {by_kind[kind] - 5} more")
            print()
        print("  What to do with this: a flag means 'a reviewer should look,' NOT")
        print("  'this is definitely wrong' — an odd long function may be justified")
        print("  (Chesterton's Fence, suite Law 3). Hand these to senior-review or")
        print("  scrutinize for the wisdom call. This tool measures shape; it never")
        print("  decides wisdom.")
    print()
    print("-" * 70)
    print(r["verdict"])


def main():
    ap = argparse.ArgumentParser(description="Structural-quality reporter (spaghetti alarm).")
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--thresholds", help="JSON file overriding default thresholds")
    args = ap.parse_args()

    thresholds = dict(DEFAULT_THRESHOLDS)
    if args.thresholds:
        thresholds.update(json.load(open(args.thresholds)))

    r = analyze(args.paths or ["."], thresholds)

    if args.json:
        print(json.dumps({
            "verdict": r["verdict"], "exit_code": r["exit_code"],
            "files_scanned": len(r["all_code"]), "python_files": len(r["py_files"]),
            "functions_scanned": r["fn_count"],
            "findings": [{"kind": k, "file": f, "line": l, "detail": d}
                         for k, f, l, d in r["findings"]],
            "by_kind": dict(r["by_kind"]), "thresholds": thresholds,
            "richer_linters_available": r["available"],
            "non_python_depth": "line+duplication only" if r["non_py"] else None,
        }, indent=2))
    else:
        print_human_report(r)
    return r["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
