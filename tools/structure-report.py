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
  7. Opaque code            — a large region the file's own parser never entered
                              (string/comment) that is nonetheless shaped like code.
                              Invisible to every signal above by construction, and
                              untestable by construction. See OPACITY below.

It checks STRUCTURE, not correctness — it cannot know if the code is right, but it
CAN catch the shapes that make code unmaintainable regardless of correctness. That
is the cheapest structural enforcement available and (for Python) it requires
nothing but the stdlib.

OPACITY (signal 7) and THE RATCHET (--baseline)
-----------------------------------------------
Both were earned by one reported miss: a file whose bulk was another language's source
held in a single string literal. To an AST that entire region is ONE node, so
complexity, nesting, and function-length all measured ZERO over the largest mass in the
file — and it was untestable by construction, since no test harness can address code
inside a string literal. Meanwhile the file had grown past maintainability through
individually-proven increments: a point-in-time gate re-asks "is this too long?" and
keeps earning the same correct "justified", so only ACCUMULATION is visible and nothing
was measuring it.

Signal 7 does NOT look for JavaScript, or for any named language — a marker list is
hard-coded knowledge that dates the moment the next language appears (Law 6, constrain
process never intelligence). It asks the two questions that have the same answer
everywhere: how much of this file did the parser refuse to enter, and is that region
shaped like code? See `structure_opacity` for the measurement and its calibration.
The consequence is reported on EVERY run as the Coverage line, because a finding count
without its denominator lets unmeasured regions read as clean.

The rule, its rationale, and the debt-ledger obligation live in PROTOCOL §10 (the
ratchet rule) and `skills/structure-gate/SKILL.md` — Law 1, every rule lives in
exactly one place. This tool is the mechanism, not the doctrine:

    structure-report.py --write-baseline .structure-baseline.json .   # accept
    structure-report.py --baseline .structure-baseline.json .         # ratchet

Baselined breaches are ACCEPTED; the run then fails only on a breach that is NEW or an
accepted one that got WORSE. That is still measurement (a number moved), never a wisdom
call, and it makes the gate usable on legacy code where an un-baselined run is red
forever — a permanently-red gate is a disabled gate. `--require-debt-ledger` refuses a
baseline whose files have no `DEBT_LEDGER.md` row: debt you did not write down is
amnesty, not acceptance.

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
    STRUCTURE: held(accepted: K, repaid: R)                        [ratchet mode]
    STRUCTURE: regressed(new: A, worse: B, top: <signal>) | review-needed
    STRUCTURE: blocked(no analyzable source found)

EXIT CODES
----------
  0 = clean, or ratchet held                — CI may pass
  1 = findings / regression                 — CI blocks; review-needed
  2 = blocked (nothing analyzable)          — CI blocks; misconfiguration

USAGE
-----
    structure-report.py [PATH ...]                  # defaults to "."
    structure-report.py --json                      # machine-readable
    structure-report.py --thresholds f.json         # override default thresholds
    structure-report.py --write-baseline b.json .   # accept today's shape
    structure-report.py --baseline b.json .         # ratchet against it
    structure-report.py --baseline b.json --require-debt-ledger .

SCOPE / HONESTY
---------------
Full depth (complexity, nesting, cycles, opacity) is implemented for Python via the
stdlib `ast` + `tokenize`. For other languages the tool falls back to file-length
and duplication signals and SAYS SO in its output rather than pretending to a depth
it does not have — derive, never fake (suite Law: evidence or downgrade). If richer
linters are installed (radon, ruff, eslint, madge) the tool notes they are available
so a future version / the harness can escalate; it never silently depends on them.
"""
import ast
import sys
import os
import json
import argparse
import shutil

import structure_opacity as opacity
from collections import defaultdict, namedtuple

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
    "opaque_span":         40,   # consecutive lines the parser never entered
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

# A finding carries its ratchet identity (symbol) and its magnitude (value) so the
# baseline can answer "is this the same breach, and did it get worse?" — line numbers
# drift on every unrelated edit and make a useless key.
Finding = namedtuple("Finding", "kind path line detail symbol value")


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


def read_text(path):
    """Source text, or None when unreadable. errors='replace' so one odd byte never
    silently drops a whole file out of the scan (which would hide its breaches)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


# ---------- language-agnostic file length ----------------------------------------
def analyze_file_length(path, thresholds, findings):
    """God-file check for EVERY code file, not just Python.

    Regression this fixes: the file-length check used to live inside the Python-only
    analyzer, so an oversized .js/.ts/.go/.rs file tripped nothing at all while the
    report's own caveat claimed other languages got 'length + duplication' signals.
    They got duplication. The caveat was false and the biggest files in a polyglot
    repo were the ones the god-file alarm could not ring on.
    """
    src = read_text(path)
    if src is None:
        return
    n = sloc(src.splitlines())
    if n > thresholds["file_lines"]:
        findings.append(Finding(
            "file_lines", path, 0,
            f"file is {n} SLoC (> {thresholds['file_lines']}) — god-file", "", n))


# ---------- opaque regions: what the parser never entered ------------------------
def find_opaque_code(path, src, thresholds, findings):
    """Flag large regions the file's own lexer classified as string/comment, when
    those regions are shaped like code. Returns the file's coverage record.

    See `structure_opacity` for the principle and PROTOCOL §10 rule 5 for the rule.
    In one line: every other signal in this tool measures ZERO over a string literal,
    so the only honest question is how much of the file the parser refused to enter —
    and that question needs no knowledge of what language is in there.
    """
    cov = opacity.measure(path, src, thresholds["opaque_span"])
    for span in cov["spans"]:
        st = span["stats"]
        findings.append(Finding(
            "opaque_code", path, span["start"],
            f"{span['lines']} lines the parser never entered "
            f"(> {thresholds['opaque_span']}), shaped like code "
            f"(indent levels {st['indent_levels']}, line-length variation "
            f"{st['length_cv']}; looks like {span['hint']}) — unreachable by any "
            f"linter, test, or complexity metric here",
            f"L{span['start']}", span["lines"]))
    return cov


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


NO_COVERAGE = {"supported": False, "total": 0, "opaque": 0,
               "documented": 0, "spans": []}


def analyze_python(path, thresholds, findings):
    src = read_text(path)
    if src is None:
        return 0, NO_COVERAGE
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        findings.append(Finding("syntax", path, 0,
                                f"file does not parse (line {e.lineno}) — cannot analyze",
                                "", 1))
        return 0, dict(NO_COVERAGE, total=len(src.splitlines()))

    cov = find_opaque_code(path, src, thresholds, findings)

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
                findings.append(Finding("function_lines", path, start,
                                        f"{n.name}() is {length} lines "
                                        f"(> {thresholds['function_lines']})", n.name, length))
            if cc > thresholds["cyclomatic"]:
                findings.append(Finding("cyclomatic", path, start,
                                        f"{n.name}() complexity {cc} "
                                        f"(> {thresholds['cyclomatic']})", n.name, cc))
            if nd > thresholds["nesting_depth"]:
                findings.append(Finding("nesting_depth", path, start,
                                        f"{n.name}() nests {nd} deep "
                                        f"(> {thresholds['nesting_depth']})", n.name, nd))
    return fn_count, cov


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
        src = read_text(path)
        if src is None:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
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
DUP_REPORT_CAP = 20


def find_duplication(paths, thresholds, findings):
    block = thresholds["duplication_block"]
    seen = defaultdict(list)  # normalized window -> [(file, lineno)]
    for path in iter_files(paths, CODE_EXT):
        src = read_text(path)
        if src is None:
            continue
        norm = [l.strip() for l in src.splitlines()]
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
        if len(locs) > 1 and reported < DUP_REPORT_CAP:
            files = ", ".join(f"{os.path.basename(f)}:{ln}" for f, ln in locs[:3])
            findings.append(Finding(
                "duplication", locs[0][0], locs[0][1],
                f"{block}-line block duplicated across {len(locs)} sites: {files}",
                "", len(locs)))
            reported += 1


# ---------- reporting ------------------------------------------------------------
SEVERITY_ORDER = ["syntax", "opaque_code", "cyclomatic", "nesting_depth",
                  "function_lines", "file_lines", "duplication", "import_cycle"]
PLAIN = {
    "syntax":            "BROKEN — file does not parse",
    "opaque_code":       ("UNSEEN CODE — a large region the parser never entered "
                          "(inside strings/comments) that is shaped like code: no test, "
                          "linter, or complexity check can reach it"),
    "cyclomatic":        "TANGLED — functions with too many branches (hardest to test, most bug-prone)",
    "nesting_depth":     "DEEP NESTING — code indented too many levels (the visual shape of spaghetti)",
    "function_lines":    "LONG FUNCTIONS — functions doing too much in one place",
    "file_lines":        "GOD-FILES — single files carrying too much",
    "duplication":       "COPY-PASTE — same block repeated in multiple places (will drift and rot)",
    "import_cycle":      "CIRCULAR DEPENDENCY — modules import each other in a loop (literal spaghetti)",
}


def _severity(kind):
    return SEVERITY_ORDER.index(kind) if kind in SEVERITY_ORDER else 99


def _safe_relpath(path):
    # os.path.relpath raises ValueError on Windows when path and cwd are on different
    # drives (e.g. scanning C:\Temp from an E:\ repo). Fall back to the absolute path.
    try:
        return os.path.relpath(path)
    except ValueError:
        return path


def analyze(paths, thresholds):
    """Measure all signals over paths; return a result dict (findings + verdict + exit code)."""
    findings = []
    py_files = list(iter_files(paths, PY_EXT))
    all_code = list(iter_files(paths, CODE_EXT))
    non_py = [f for f in all_code if os.path.splitext(f)[1] not in PY_EXT]

    for path in all_code:                                      # god-files (all languages)
        analyze_file_length(path, thresholds, findings)

    # Coverage accounting. A finding count is not a result without the denominator it
    # was measured over (PROTOCOL §10 rule 5): a region the analyzer never entered is
    # UNMEASURED, and in a report that omits coverage, unmeasured reads as clean.
    fn_count, entered, opaque, documented = 0, 0, 0, 0
    for path in py_files:                                      # deep signals (python)
        n, cov = analyze_python(path, thresholds, findings)
        fn_count += n
        entered += max(cov["total"] - cov["opaque"] - cov["documented"], 0)
        opaque += cov["opaque"]
        documented += cov["documented"]
    shallow = sum(len((read_text(p) or "").splitlines()) for p in non_py)
    # Denominator is CODE: docstrings and comments are declared prose, not blind spots.
    code_lines = entered + opaque + shallow
    coverage = {"entered": entered, "opaque": opaque, "shallow": shallow,
                "documented": documented, "code_lines": code_lines,
                "pct_entered": round(100 * entered / code_lines, 1) if code_lines else 0.0}

    for c in find_cycles(python_import_graph(paths)):          # import cycles (python)
        findings.append(Finding("import_cycle", c[0], 0,
                                "import cycle: " + " -> ".join(c),
                                "->".join(sorted(set(c))), len(set(c))))

    find_duplication(paths, thresholds, findings)              # duplication (all languages)

    # richer linters present-but-unused: note, never depend.
    available = [t for t in ("radon", "ruff", "eslint", "madge") if shutil.which(t)]

    by_kind = defaultdict(int)
    for f in findings:
        by_kind[f.kind] += 1

    if not all_code:
        verdict, exit_code = "STRUCTURE: blocked(no analyzable source found)", 2
    elif not findings:
        verdict = f"STRUCTURE: clean({len(all_code)} files, {fn_count} functions scanned)"
        exit_code = 0
    else:
        top = min(by_kind, key=_severity)
        verdict = f"STRUCTURE: findings(top: {top}, count: {len(findings)}) | review-needed"
        exit_code = 1

    return {"findings": findings, "by_kind": by_kind, "all_code": all_code,
            "py_files": py_files, "non_py": non_py, "fn_count": fn_count,
            "available": available, "verdict": verdict, "exit_code": exit_code,
            "thresholds": thresholds, "ratchet": None, "coverage": coverage}


# ---------- the ratchet ----------------------------------------------------------
# Aggregation rule per signal. The baseline key must survive unrelated edits, so it is
# (kind, file, symbol) — never a line number — and the value is the magnitude that
# "got worse" is measured against.
AGGREGATE = {"duplication": "count", "opaque_code": "sum"}   # default: "max"
BASELINE_VERSION = 1


def _key(f):
    return f"{f.kind}|{_safe_relpath(f.path).replace(os.sep, '/')}|{f.symbol}"


def signature_map(findings):
    """Ratchet identity -> magnitude, aggregated per signal (module docstring: THE RATCHET)."""
    agg = {}
    for f in findings:
        k, rule = _key(f), AGGREGATE.get(f.kind, "max")
        inc = 1 if rule == "count" else f.value
        agg[k] = max(agg.get(k, inc), inc) if rule == "max" else agg.get(k, 0) + inc
    return agg


def _ledger_coverage(findings, ledger_path):
    """Files carrying baselined debt that DEBT_LEDGER.md does not mention.

    A baseline with no repayment plan is permanent amnesty; the ledger is what turns
    an accepted breach into a debt with a trigger (PROTOCOL §3, owner structure-gate).
    """
    try:
        with open(ledger_path, encoding="utf-8-sig") as fh:
            text = fh.read()
    except OSError:
        return None  # no ledger present — caller decides whether that is fatal
    missing = set()
    for f in findings:
        rel = _safe_relpath(f.path).replace(os.sep, '/')
        if rel not in text and os.path.basename(rel) not in text:
            missing.add(rel)
    return sorted(missing)


def apply_ratchet(r, baseline, ledger_path=None, require_ledger=False):
    """Re-decide the verdict against an accepted baseline: direction, not acceptability.

    This stays inside the skill's 'measure, never judge' contract. The ratchet never
    claims a baselined breach is wrong — Chesterton's Fence (Law 3) still protects it.
    It asserts only that the number went UP, which is a measurement.
    """
    if r["exit_code"] == 2:
        return r  # nothing analyzable — the baseline is irrelevant

    current = signature_map(r["findings"])
    accepted = baseline.get("entries", {})
    new = {k: v for k, v in current.items() if k not in accepted}
    worse = {k: (v, accepted[k]) for k, v in current.items()
             if k in accepted and v > accepted[k]}
    repaid = {k: v for k, v in accepted.items() if k not in current}
    held = {k: v for k, v in current.items() if k in accepted and v <= accepted[k]}

    unledgered = _ledger_coverage(r["findings"], ledger_path) if ledger_path else None
    ledger_breach = require_ledger and (unledgered is None or unledgered)

    r["ratchet"] = {"new": new, "worse": worse, "repaid": repaid, "held": held,
                    "unledgered": unledgered, "ledger_path": ledger_path,
                    "require_ledger": require_ledger, "ledger_breach": ledger_breach,
                    "baseline_entries": len(accepted)}

    if new or worse:
        kinds = [k.split("|")[0] for k in list(new) + list(worse)]
        top = min(set(kinds), key=_severity)
        r["verdict"] = (f"STRUCTURE: regressed(new: {len(new)}, worse: {len(worse)}, "
                        f"top: {top}) | review-needed")
        r["exit_code"] = 1
    elif ledger_breach:
        r["verdict"] = ("STRUCTURE: regressed(new: 0, worse: 0, "
                        "top: unledgered-debt) | review-needed")
        r["exit_code"] = 1
    else:
        r["verdict"] = f"STRUCTURE: held(accepted: {len(held)}, repaid: {len(repaid)})"
        r["exit_code"] = 0
    return r


def write_baseline(r, path):
    payload = {"version": BASELINE_VERSION,
               "thresholds": r["thresholds"],
               "note": ("Accepted structural debt. Each entry must have a row in "
                        "DEBT_LEDGER.md naming why it was accepted, what it costs per "
                        "future change, and the trigger that makes repayment due. "
                        "Regenerate only when debt is REPAID — never to silence a "
                        "regression (that is how the ratchet gets disabled)."),
               "entries": signature_map(r["findings"])}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return payload


# ---------- human report ---------------------------------------------------------
def _print_findings_by_kind(findings, by_kind):
    for kind in sorted(by_kind, key=_severity):
        print(f"  ── {PLAIN.get(kind, kind)}  ({by_kind[kind]})")
        for f in [x for x in findings if x.kind == kind][:5]:
            loc = _safe_relpath(f.path) + (f":{f.line}" if f.line else "")
            print(f"       · {f.detail}   [{loc}]")
        if by_kind[kind] > 5:
            print(f"       … and {by_kind[kind] - 5} more")
        print()


def _print_ratchet(rt):
    print(f"  RATCHET — measured against {rt['baseline_entries']} accepted breach(es) "
          "in the baseline.")
    print("  The baseline does not say the accepted debt is fine; it says the debt is")
    print("  KNOWN. This run only asks whether anything got worse.\n")
    if rt["new"]:
        print(f"  ⛔  {len(rt['new'])} NEW breach(es) — not in the baseline:")
        for k, v in list(rt["new"].items())[:8]:
            kind, path, sym = k.split("|", 2)
            print(f"       · {kind} = {v}   [{path}{(' :: ' + sym) if sym else ''}]")
        print()
    if rt["worse"]:
        print(f"  ⛔  {len(rt['worse'])} accepted breach(es) GOT WORSE:")
        for k, (now, was) in list(rt["worse"].items())[:8]:
            kind, path, sym = k.split("|", 2)
            print(f"       · {kind}: {was} → {now}   [{path}{(' :: ' + sym) if sym else ''}]")
        print()
    if rt["repaid"]:
        print(f"  ✅  {len(rt['repaid'])} baselined breach(es) REPAID — gone from the source.")
        print("      Re-run --write-baseline to lock the improvement in.\n")
    if rt["ledger_path"]:
        un = rt["unledgered"]
        if un is None:
            print(f"  ⚠️  No debt ledger at {rt['ledger_path']} — the baseline is currently")
            print("      permanent amnesty. Every accepted breach needs a repayment trigger.\n")
        elif un:
            print(f"  ⚠️  {len(un)} file(s) carry accepted debt with no DEBT_LEDGER.md row:")
            for p in un[:8]:
                print(f"       · {p}")
            print()
        else:
            print("  ✅  Every file carrying accepted debt is listed in the debt ledger.\n")
    if not (rt["new"] or rt["worse"] or rt["ledger_breach"]):
        print("  ✅  HELD — nothing got worse. Known debt did not grow.")


def print_human_report(r):
    rt = r.get("ratchet")
    print("=" * 70)
    print("STRUCTURAL QUALITY REPORT  —  is this spaghetti?")
    print("=" * 70)
    print(f"Scanned: {len(r['all_code'])} code files "
          f"({len(r['py_files'])} Python, deep-analyzed; "
          f"{len(r['non_py'])} other, length+duplication only) · {r['fn_count']} functions")
    c = r["coverage"]
    print(f"Coverage: {c['code_lines']:,} code lines · {c['pct_entered']}% actually "
          f"entered by a parser · {c['opaque']:,} opaque\n          (inside string "
          f"literals) · {c['shallow']:,} shallow (no parser for that language here) · "
          f"{c['documented']:,} docs")
    if c["pct_entered"] < 100:
        print("          Everything below was measured over the entered portion ONLY. The")
        print("          rest is unmeasured, which is not the same as clean.")
    if r["non_py"]:
        print("  note: complexity, nesting, cycle and opacity analysis is Python-only in "
              "this\n        version; other languages get file-length and duplication "
              "signals only.")
    if r["available"]:
        print(f"  note: richer linters available on PATH ({', '.join(r['available'])}) — "
              "the harness\n        may escalate to them for deeper signal.")
    print()

    if rt:
        _print_ratchet(rt)
    elif not r["findings"]:
        print("  ✅  CLEAN — no structural threshold breached.")
        print("      No god-files, no tangled functions, no circular imports, no")
        print("      copy-paste blocks, no foreign language hidden in a string.")
        print("      (This is a STRUCTURE verdict, not a correctness or wisdom verdict —")
        print("       senior-review and correctness-gate still own those.)")
    else:
        print(f"  ⚠️  REVIEW NEEDED — {len(r['findings'])} structural flag(s), by category:\n")
        _print_findings_by_kind(r["findings"], r["by_kind"])
        print("  What to do with this: a flag means 'a reviewer should look,' NOT")
        print("  'this is definitely wrong' — an odd long function may be justified")
        print("  (Chesterton's Fence, suite Law 3). Hand these to senior-review or")
        print("  scrutinize for the wisdom call. This tool measures shape; it never")
        print("  decides wisdom.")
        print()
        print("  On an existing codebase this list is a starting position, not a")
        print("  sentence: record it with --write-baseline, give every entry a row in")
        print("  DEBT_LEDGER.md, and run --baseline from then on so the debt is frozen")
        print("  where it stands and cannot grow by defensible increments.")
    print()
    print("-" * 70)
    print(r["verdict"])


def json_report(r):
    rt = r.get("ratchet")
    out = {
        "verdict": r["verdict"], "exit_code": r["exit_code"],
        "files_scanned": len(r["all_code"]), "python_files": len(r["py_files"]),
        "coverage": r["coverage"],
        "functions_scanned": r["fn_count"],
        "findings": [{"kind": f.kind, "file": f.path, "line": f.line,
                      "detail": f.detail, "symbol": f.symbol, "value": f.value}
                     for f in r["findings"]],
        "by_kind": dict(r["by_kind"]), "thresholds": r["thresholds"],
        "richer_linters_available": r["available"],
        "non_python_depth": "length+duplication only" if r["non_py"] else None,
        "duplication_report_cap": DUP_REPORT_CAP,
    }
    if rt:
        out["ratchet"] = {
            "baseline_entries": rt["baseline_entries"],
            "new": rt["new"], "worse": {k: {"now": n, "was": w}
                                        for k, (n, w) in rt["worse"].items()},
            "repaid": rt["repaid"], "held": len(rt["held"]),
            "unledgered_files": rt["unledgered"], "ledger_breach": rt["ledger_breach"],
        }
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Structural-quality reporter (spaghetti alarm) with a debt ratchet.")
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--thresholds", help="JSON file overriding default thresholds")
    ap.add_argument("--baseline", metavar="FILE",
                    help="ratchet against accepted debt: fail only on new or worsened breaches")
    ap.add_argument("--write-baseline", metavar="FILE",
                    help="record today's breaches as accepted debt, then exit 0")
    ap.add_argument("--debt-ledger", metavar="FILE", default="DEBT_LEDGER.md",
                    help="ledger that must account for baselined debt (default: DEBT_LEDGER.md)")
    ap.add_argument("--require-debt-ledger", action="store_true",
                    help="fail when baselined debt is not listed in the debt ledger")
    args = ap.parse_args()

    thresholds = dict(DEFAULT_THRESHOLDS)
    if args.thresholds:
        with open(args.thresholds, encoding="utf-8") as fh:
            thresholds.update(json.load(fh))

    r = analyze(args.paths or ["."], thresholds)

    if args.write_baseline:
        payload = write_baseline(r, args.write_baseline)
        print(f"structure-report: wrote {len(payload['entries'])} accepted breach(es) "
              f"to {args.write_baseline}")
        print("Next: give every file listed there a DEBT_LEDGER.md row (what, why "
              "accepted,\ncost per future change, trigger that makes repayment due), "
              "then run with\n--baseline so the debt is frozen where it stands.")
        print("\n" + f"STRUCTURE: held(accepted: {len(payload['entries'])}, repaid: 0)")
        return 0

    if args.baseline:
        try:
            with open(args.baseline, encoding="utf-8-sig") as fh:
                baseline = json.load(fh)
        except (OSError, ValueError) as e:
            print(f"structure-report: cannot read baseline {args.baseline}: {e}")
            print("STRUCTURE: blocked(no analyzable source found)")
            return 2
        r = apply_ratchet(r, baseline, ledger_path=args.debt_ledger,
                          require_ledger=args.require_debt_ledger)

    if args.json:
        print(json.dumps(json_report(r), indent=2))
    else:
        print_human_report(r)
    return r["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
