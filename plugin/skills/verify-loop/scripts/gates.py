"""gates.py — rules the model used to be asked to follow, turned into verdicts.

Each gate takes what an agent wrote or did and says whether it holds. None of them asks the agent
what it meant. verify.py calls them; they never write state.

  answer-check   the agent's final answer states the verdict, claims nothing the state does not
                 show, and names every gap `report` lists                        (ANSWER ...)
  unmapped       product source files no feature's path:, command, oracle or check imports
                 reach, and no blind spot names                                   (UNMAPPED)
  weak signal    a fail-signal that names no behavior: runner boilerplate such as FAILED or
                 AssertionError, which any failure prints                         (WEAK SIGNAL)
  where          a failure receipt counts only if the files differed from today's in the
                 product (inside `path:` when the feature has one): a red with no product
                 difference came from the environment, not from a wrong result   (PROOF NOT FROM PRODUCT)
  loosened       a test whose exact assertions became tolerant or vanished, or whose expected
                 literals changed, in git history or the working tree            (LOOSENED)
  blocked        a failing check whose output is a missing tool, dependency, port or timeout:
                 report it as blocked, never fix product code for it             (BLOCKED)
"""
import ast
import os
import re
import subprocess


# ---- weak fail-signal ---------------------------------------------------------------------
# A signal must say what was wrong. Strip the words every failing runner prints; something must
# remain: a number, or a word of three letters or more.

GENERIC = set("""
fail fails failed failing failure failures error errors err exception exceptions assertionerror
assert asserts assertion assertions traceback exit exited code status nonzero non zero false true none
null nil test tests testing not ok fatal panic red check checks expected got actual or and the a an
of to is was in on at by with value result output returned return
""".split())


RUNNER_NUMBERS = re.compile(r"(?i)\b(?:exit(?:ed)?(?:\s+with)?(?:\s+(?:code|status))?|return\s?code|line)"
                            r"\s*[:=]?\s*-?\d+|\b\d+\s+(?:failed|passed|errors?|failures?|tests?)\b")


def weak_signal(signal):
    """Why this fail-signal names no behavior, or None when it does."""
    words = [w for w in re.split(r"[^A-Za-z0-9]+", RUNNER_NUMBERS.sub(" ", signal or "")) if w]
    content = [w for w in words if w.lower() not in GENERIC]
    if any(w.isdigit() for w in content) or sum(len(w) for w in content) >= 3:
        return None
    return ("it names no behavior: any failing run prints it. Write the wrong result the spec "
            "rules out, e.g. `expected total 189, got 188`")


# ---- product files and what reaches them --------------------------------------------------

SOURCE_EXT = (".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rb", ".java", ".kt", ".rs",
              ".swift", ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".php", ".scala")
CONFIG_NAMES = {"setup.py", "conftest.py", "noxfile.py", "fabfile.py", "manage.py"}
CONFIG_RX = re.compile(r"\.(config|conf|rc)\.(js|cjs|mjs|ts)$|\.d\.ts$")


def is_product(v, repo, rel):
    """A source file the product is made of: not a test, a config file or hidden tooling."""
    parts = rel.split("/")
    base = parts[-1]
    if not base.endswith(SOURCE_EXT) or base in CONFIG_NAMES or CONFIG_RX.search(base):
        return False
    if any(p.startswith(".") or p in v.SKIP_DIRS or p in v.GENERIC_DIRS for p in parts[:-1]):
        return False
    if v.is_test_file(rel) or v.TEST_JS.match(base) or v.TEST_GO.match(base):
        return False
    if base.endswith(".py") and not _defines_anything(v, repo, rel):
        return False  # an empty __init__.py or a constants-only module is not behavior
    return True


def _defines_anything(v, repo, rel):
    try:
        tree = ast.parse(v.read(repo, rel))
    except (SyntaxError, ValueError, OSError):
        return True
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for n in ast.walk(tree))


def under(rel, prefix):
    p = prefix.strip().strip("`").rstrip("/").replace("\\", "/")
    p = p[2:] if p.startswith("./") else p
    return bool(p) and (rel == p or rel.startswith(p + "/"))


def _py_imports(text, rel):
    """Module names a Python file imports, relative ones made absolute from its folder."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return []
    pkg = rel.rsplit("/", 1)[0].replace("/", ".") if "/" in rel else ""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                parts = pkg.split(".") if pkg else []
                parts = parts[:len(parts) - (n.level - 1)] if n.level > 1 else parts
                base = ".".join(p for p in parts + ([n.module] if n.module else []) if p)
            else:
                base = n.module or ""
            out.append(base)
            out += [f"{base}.{a.name}" if base else a.name for a in n.names]
    return out


def _py_resolve(repo, mod, rel):
    """Repo files a module name can mean: from the repo root, or from the importing file's folder."""
    found = []
    here = rel.rsplit("/", 1)[0] if "/" in rel else ""
    for root in {"", here}:
        stem = "/".join(x for x in (root, mod.replace(".", "/")) if x)
        for cand in (stem + ".py", stem + "/__init__.py"):
            if os.path.isfile(os.path.join(repo, cand)):
                found.append(cand)
    return found


JS_IMPORT = re.compile(r"""(?:from\s+|require\s*\(\s*|import\s*\(\s*|import\s+)['"](\.{1,2}/[^'"]+)['"]""")


def _js_resolve(repo, spec, rel):
    here = rel.rsplit("/", 1)[0] if "/" in rel else ""
    stem = os.path.normpath(os.path.join(here, spec)).replace("\\", "/")
    for cand in (stem, *(stem + e for e in (".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs")),
                 *(stem + "/index" + e for e in (".js", ".ts", ".tsx", ".jsx"))):
        if os.path.isfile(os.path.join(repo, cand)):
            return [cand]
    return []


def reached(v, repo, start):
    """Every repo file the files in `start` import, transitively (Python and relative JS imports)."""
    seen, todo = set(), list(start)
    while todo:
        rel = todo.pop()
        if rel in seen or not os.path.isfile(os.path.join(repo, rel)):
            continue
        seen.add(rel)
        try:
            text = v.read(repo, rel)
        except OSError:
            continue
        if rel.endswith(".py"):
            for mod in _py_imports(text, rel):
                todo += _py_resolve(repo, mod, rel)
        elif rel.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")):
            for spec in JS_IMPORT.findall(text):
                todo += _js_resolve(repo, spec, rel)
    return seen


def excused(rel, blind):
    """True when a `## Blind spots` line names the file or a folder holding it."""
    for line in blind:
        for tok in re.findall(r"`([^`]+)`|([\w./-]+[/.][\w./-]*)", line):
            t = tok[0] or tok[1]
            if under(rel, t):
                return True
    return False


def unmapped(v, repo, features, blind):
    """Product files nothing in VERIFY.md reaches and no blind spot names, sorted."""
    files = [rel for rel, _ in v.tree_files(repo)]
    commands = [c for f in features for _, c in f["checks"]]
    paths = [p for f in features for p in f.get("paths") or []]
    frozen = {o.strip().replace("\\", "/") for f in features for o in f.get("oracles") or []}
    named = {rel for rel in files if any(re.search(rf"(?:^|[\s'\"`=])(?:\./)?{re.escape(rel)}(?:$|[\s'\"`;)])", c)
                                         for c in commands)}
    tests = [t for t in v.find_tests(repo) if v.is_covered(t, commands, repo)]
    covmap = v.read_json(v.coverage_path(repo)) or {}
    covered = {x for e in covmap.values() if isinstance(e, dict) for x in e.get("files", [])}
    reach = reached(v, repo, set(tests) | named | (frozen & set(files)))
    out = []
    for rel in files:
        if not is_product(v, repo, rel):
            continue
        if rel in reach or rel in named or rel in frozen or rel in covered or any(under(rel, p) for p in paths):
            continue
        if excused(rel, blind):
            continue
        out.append(rel)
    return sorted(out)


# ---- where the wrong state was ------------------------------------------------------------

def where_problem(v, repo, feature, receipt, now, frozen):
    """Why this failure receipt does not show the check rejecting a wrong product, or None.
    `now` is file_sigs(repo) today; the receipt's `files` is file_sigs when it went red."""
    if receipt.get("mutation"):
        return None  # a caught challenge mutated a product file in a scratch copy by design
    then = receipt.get("files")
    if not isinstance(then, dict):
        return "the receipt does not record the files it failed on (made before 1.18.0): prove it again"
    skip = set(frozen) | {v.RECIPE}
    diff = sorted(r for r in set(then) | set(now) if then.get(r) != now.get(r) and r not in skip
                  and not v.is_test_file(r) and not r.endswith(".md"))
    paths = feature.get("paths") or []
    if diff and paths:
        if any(under(r, p) for r in diff for p in paths):
            return None
        where = ", ".join(diff[:5])
        return (f"when it went red, the files differed from today's in {where}, none inside its path: "
                f"{', '.join(paths)}. Put the wrong result in the product, run, restore")
    if diff:
        return None
    return ("it went red on the same files that pass today: the red came from the environment (a tool, "
            "the network, a flake), not from a wrong result. Put the wrong result in the product, run, restore")


# ---- loosened tests -----------------------------------------------------------------------

EXACT_PY = re.compile(r"^assert(?:Equal|Equals|ListEqual|DictEqual|TupleEqual|SetEqual|SequenceEqual|"
                      r"MultiLineEqual|CountEqual|Is|IsNone|Raises|RaisesRegex)$")
TOLERANT_KW = {"delta", "places", "rel_tol", "abs_tol", "rel", "abs", "atol", "rtol"}


def _consts(node):
    """The literal values in an assertion: what it expects."""
    return [repr(n.value) for n in ast.walk(node)
            if isinstance(n, ast.Constant) and not (isinstance(n.value, str) and len(n.value) >= 80)]


def _py_strength(text):
    """{test name: (exact assertions, their literal arguments)} for a Python test file, or None."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return None
    out = {}

    def take(fn, name):
        exact, lits = 0, []
        for n in ast.walk(fn):
            if isinstance(n, ast.Assert) and isinstance(n.test, ast.Compare) and \
                    all(isinstance(o, (ast.Eq, ast.Is)) for o in n.test.ops) and \
                    "approx" not in ast.dump(n.test):
                exact += 1
                lits += _consts(n.test)
            elif isinstance(n, ast.Call):
                name_ = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
                if EXACT_PY.match(name_ or "") and not any(k.arg in TOLERANT_KW for k in n.keywords) and \
                        "approx" not in ast.dump(n):
                    exact += 1
                    for a in n.args[:2]:  # (actual, expected); a third is the failure message
                        lits += _consts(a)
        out[name] = (exact, sorted(lits))

    defs = (ast.FunctionDef, ast.AsyncFunctionDef)
    for node in tree.body:
        if isinstance(node, defs) and node.name.startswith("test"):
            take(node, node.name)
        elif isinstance(node, ast.ClassDef):
            for m in node.body:
                if isinstance(m, defs) and m.name.startswith("test"):
                    take(m, f"{node.name}.{m.name}")
    return out


EXACT_JS = re.compile(r"\.(?:toBe|toEqual|toStrictEqual|toHaveLength|toThrow)\s*\(|\bassert\.(?:equal|strictEqual|deepEqual|deepStrictEqual|throws)\s*\(")


def _js_strength(v, text):
    found = {}
    for m in re.finditer(r"(?m)(?:^|[;{]\s*)(?:it|test)\s*\(\s*(['\"`])((?:\\.|(?!\1).)+)\1", text):
        body = v._balanced_body(text, m.start(), "(", ")") or ""
        exact = EXACT_JS.findall(body)
        lits = re.findall(r"\.(?:toBe|toEqual|toStrictEqual|toHaveLength)\s*\(\s*([^()]{0,60})\)", body)
        found[m.group(2)] = (len(exact), sorted(lits))
    return found


def strength(v, text, rel):
    base = rel.rsplit("/", 1)[-1]
    if text is None:
        return None
    if v.TEST_JS.match(base):
        return _js_strength(v, text)
    if base.endswith(".py"):
        return _py_strength(text)
    return None


def compare(v, before, after, rel):
    """[(test, detail)] where `after` is weaker than `before` for the same file."""
    old_rows = v.tests_in_text(before, rel) if before is not None else None
    new_rows = v.tests_in_text(after, rel) if after is not None else None
    if old_rows is None:
        return []
    if new_rows is None:
        return [("*", "the file no longer parses")]
    now = {name: (skip, count) for name, _, skip, count in new_rows}
    old_s, new_s = strength(v, before, rel) or {}, strength(v, after, rel) or {}
    out = []
    for name, _, skip, count in old_rows:
        if name not in now:
            out.append((name, "removed"))
            continue
        n_skip, n_count = now[name]
        if n_skip and not skip:
            out.append((name, "now skipped"))
        elif n_count < count:
            out.append((name, f"{count} -> {n_count} assertions"))
        elif name in old_s and name in new_s:
            (e0, l0), (e1, l1) = old_s[name], new_s[name]
            if e1 < e0:
                out.append((name, f"{e0} -> {e1} exact assertions (equality made tolerant or vague)"))
            elif e1 == e0 and l0 != l1:
                out.append((name, f"expected values changed: {', '.join(l0)[:80]} -> {', '.join(l1)[:80]}"))
    return out


def _git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True)
    return p.stdout.decode("utf-8", errors="replace") if p.returncode == 0 else None


HISTORY = 30  # commits per test file looked at


def loosened(v, repo, test_files):
    """[{id, file, test, detail, commit, author, subject}] for every weakening of a mapped test file
    in its last HISTORY commits and in the working tree. Not a git repo: working tree only, so none."""
    if _git(repo, "rev-parse", "--is-inside-work-tree") is None:
        return []
    prefix = (_git(repo, "rev-parse", "--show-prefix") or "").strip()
    out = []
    for rel in test_files:
        git_rel = prefix + rel
        log = _git(repo, "log", f"-n{HISTORY}", "--format=%H%x09%an%x09%s", "--", rel) or ""
        steps = []
        head = _git(repo, "show", f"HEAD:{git_rel}")
        try:
            work = v.read(repo, rel)
        except OSError:
            work = None
        if head is not None and work != head:
            steps.append(("working tree", "you", "uncommitted", head, work))
        for line in log.splitlines():
            sha, author, subject = (line.split("\t") + ["", ""])[:3]
            after = _git(repo, "show", f"{sha}:{git_rel}")
            before = _git(repo, "show", f"{sha}^:{git_rel}")
            if before is not None:
                steps.append((sha[:10], author, subject, before, after))
        for commit, author, subject, before, after in steps:
            for test, detail in compare(v, before, after, rel):
                out.append({"id": f"{rel}|{test}|{detail}", "file": rel, "test": test, "detail": detail,
                            "commit": commit, "author": author, "subject": subject[:80]})
    return out


def loosened_text(x):
    return (f"{x['file']}::{x['test']}: {x['detail']} in {x['commit']} by {x['author']}"
            + (f" ({x['subject']})" if x["subject"] else ""))


# ---- blocked checks -----------------------------------------------------------------------

def blocked(v, out, code):
    """A one-line cause when a failing check's output is the environment (tool, dependency, port,
    timeout, connection), else None."""
    category, summary, _ = v.diagnose_failure(out, code, "")
    return summary if category == "harness-gap" else None


# ---- the answer check ---------------------------------------------------------------------

OVERCLAIM = ("verdict: green", "verify-state: green", "fully verified", "is verified", "are verified",
             "all verified", "verified and done", "proven to work", "proven correct", "ready to merge",
             "ready to ship", "safe to ship", "safe to merge", "good to go", "ship it", "lgtm",
             "can go out", "all checks pass", "everything passes", "task is done", "work is done")
NEGATION = re.compile(r"(?:\bnot|n't|\bno|\bnever|\bnor|\bcannot)\W+(?:\w+\W+){0,2}$", re.I)


def _says(text, item):
    """`item` appears in `text` as a whole word or path, not inside another word."""
    item = item.strip().lower()
    return bool(item) and re.search(rf"(?<![\w./-]){re.escape(item)}(?![\w-])", text) is not None


def _says_blind(text, item):
    if _says(text, item):
        return True
    words = [w for w in re.findall(r"[A-Za-z0-9_]{4,}", item.lower())]
    return bool(words) and sum(_says(text, w) for w in words) * 2 >= len(words)


FILL = re.compile(r"\[\[fill:[^\]]*\]\]")

# (gaps key, label): the order and words `report` and the draft print each gap with.
GAP_LABELS = (("failing", "failing check"), ("blocked", "blocked by the environment"), ("unverified", "no check"),
              ("unproven", "never seen red"), ("weak_signal", "weak signal"),
              ("proof_not_from_product", "proof not from product"), ("loosened", "loosened"),
              ("survived", "survived a wrong result"), ("unmapped", "unmapped"), ("orphan_tests", "orphan test"),
              ("unchallenged", "unchallenged"),
              ("not_independent", "not independent"), ("blind_spots", "blind spot"),
              ("rebaselined", "check changed under review"))


def gap_rows(a):
    return [(label, item) for key, label in GAP_LABELS for item in a["gaps"][key]]


def survey_caught(a):
    """What an `assess` survey saw go red, as `Total caught 2/2 wrong results; ...`, or ''."""
    return "; ".join(f"{s['feature']} caught {s['caught']}/{s['decided']} wrong results"
                     for s in a.get("surveyed") or [] if s["caught"])


def draft(a):
    """An answer that passes `check_answer` once each [[fill: ...]] holds the agent's own words.
    The helper writes what it knows; the slots are only what needs judgment."""
    lines = [f"VERDICT: {a['verdict']}",
             "Claim: [[fill: the claim in product terms, and where its expected result comes from]]"]
    for r in a["rejections"]:
        lines.append(f"Proven: {r['feature']} went red on {r['wrong_state']} (`{r['command']}`, "
                     f"signal: {r['fail_signal']})")
    seen = survey_caught(a)
    if not a["rejections"] and seen:
        lines.append(f"Proven: {seen} in assess's scratch copies; that is not a fail-proof receipt, "
                     "so the GAP lines below stand")
    elif not a["rejections"]:
        lines.append("Proven: nothing yet; no check here has been seen rejecting a wrong result")
    for p in a["passed"]:
        lines.append(f"Passed: {p['feature']} (`{p['command']}`)")
    lines += [f"GAP {label}: {item}" for label, item in gap_rows(a)]
    if a["gaps"].get("survived"):
        lines.append("Survivors: [[fill: for each, a real gap in the check or an equivalent mutation, and why]]")
    if a["verdict"] == "green":
        lines.append("Covers: the mapped features only; behavior no check exercises is not covered")
    else:
        lines.append("Next: [[fill: what is left for each GAP, and who does it]]")
    return "\n".join(lines) + "\n"


def check_answer(a, answer_text):
    """Problems with an answer against the helper's own answer `a`: [(kind, detail, fix)]. Each fix is
    a line that clears the problem as written, so a rejected agent edits instead of guessing."""
    text = answer_text.lower()
    flat = re.sub(r"[*`]", "", text)
    problems = []
    verdict = a["verdict"]
    if not re.search(rf"verdict\W{{0,4}}\s*{re.escape(verdict)}\b", flat):
        problems.append(("NO VERDICT", f"say `VERDICT: {verdict}` as `report` does", f"VERDICT: {verdict}"))
    if FILL.search(answer_text):
        problems.append(("UNFILLED", "a [[fill: ...]] slot from the draft is still there",
                         "replace each [[fill: ...]] with your own words"))
    if verdict != "green":
        for phrase in OVERCLAIM:
            for m in re.finditer(re.escape(phrase), flat):
                if not NEGATION.search(flat[max(0, m.start() - 40):m.start()]):
                    problems.append(("OVERCLAIM", f"\"{phrase}\" while the verdict is {verdict}",
                                     f"take back \"{phrase}\", or negate it (\"not {phrase}\")"))
                    break
    g = a["gaps"]
    wants = []
    for key in ("failing", "unverified", "unproven"):
        wants += [(key, item.split("|", 1)[0]) for item in g.get(key, [])]
    wants += [("blocked", item.split("|", 1)[0]) for item in g.get("blocked", [])]
    wants += [("orphan test", t) for t in g.get("orphan_tests", [])]
    wants += [("unmapped", t) for t in g.get("unmapped", [])]
    wants += [("survived", item.split(":", 1)[0]) for item in g.get("survived", [])]
    wants += [("weak signal", item.split(":", 1)[0]) for item in g.get("weak_signal", [])]
    wants += [("loosened", item.split("::", 1)[0]) for item in g.get("loosened", [])]
    wants += [("not independent", item.split(" (", 1)[0]) for item in g.get("not_independent", [])]
    wants += [("check changed under review", item.split(":", 1)[0]) for item in g.get("rebaselined", [])]
    for label, item in wants:
        base = item.rsplit("/", 1)[-1]
        if not (_says(flat, item) or (base != item and _says(flat, base))):
            problems.append(("MISSING", f"{label}: {item}", f"GAP {label}: {item}"))
    if g.get("unchallenged") and "challeng" not in flat:
        what = "unchallenged: no caught challenge mutation for the current checks"
        problems.append(("MISSING", what, f"GAP {what}"))
    for b in g.get("blind_spots", []):
        if not _says_blind(flat, b):
            problems.append(("MISSING", f"blind spot: {b}", f"GAP blind spot: {b}"))
    seen, out = set(), []
    for p in problems:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out
