"""challenge --auto: generate standard single-line mutations for one product file and judge each
against one feature's checks. The result is a mutation score for that feature.

Speed: the tree is copied once per lane (`--jobs N` lanes run in parallel), the unmutated checks
run once per lane, and each mutation is written into the lane, judged and reverted in place. A
lane whose checks leave the tree changed is recopied before the next mutation.

Generated mutations are not spec-backed, so a caught one never becomes a fail-proof receipt;
a survivor is a lead for a person to judge (a real gap, or an equivalent mutation). A survivor on
a line no check reaches (a probe that aborts there still passes) is reported as uncovered.

--diff [REF] mutates only the lines changed since REF (default HEAD): in the named file, or with no
file in every changed product file (tests, oracles, the recipe and unknown languages are skipped)."""
import ast
import contextlib
import io
import json
import os
import queue
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# (name, pattern, replacement). Applied to the first match on a line; one mutation per operator per line.
OPERATORS = [
    ("strict-eq-to-ne", r"===", "!=="),
    ("strict-ne-to-eq", r"!==", "==="),
    ("eq-to-ne", r"==", "!="),
    ("ne-to-eq", r"!=", "=="),
    ("le-to-lt", r"<=", "<"),
    ("ge-to-gt", r">=", ">"),
    ("lt-to-le", r"(?<![<=!-])<(?![<=])", "<="),
    ("gt-to-ge", r"(?<![>=-])>(?![>=])", ">="),
    ("and-to-or", r"\band\b|&&", lambda m: "or" if m.group(0) == "and" else "||"),
    ("or-to-and", r"\bor\b|\|\|", lambda m: "and" if m.group(0) == "or" else "&&"),
    ("true-to-false", r"\bTrue\b|\btrue\b", lambda m: "False" if m.group(0) == "True" else "false"),
    ("false-to-true", r"\bFalse\b|\bfalse\b", lambda m: "True" if m.group(0) == "False" else "true"),
    ("plus-to-minus", r"(?<=\s)\+(?=\s)", "-"),
    ("minus-to-plus", r"(?<=\s)-(?=\s)", "+"),
    ("mul-to-div", r"(?<=\s)\*(?=\s)", "/"),
    ("int-off-by-one", r"(?<![\w.])(\d+)(?![\w.])", lambda m: str(int(m.group(1)) + 1)),
    ("not-dropped", r"\bnot\s+", ""),
    ("is-to-is-not", r"\bis\b(?!\s*not\b)", "is not"),
    ("return-to-none", r"^\s*return\s+(?!None\b|\(\s*\)|$)(.+)$", lambda m: m.group(0).replace(m.group(1), "None")),
    ("nullish-to-or", r"\?\?", "||"),
    ("go-err-nil-flip", r"err\s*!=\s*nil", "err == nil"),
    ("go-err-eq-flip", r"err\s*==\s*nil", "err != nil"),
    ("rust-is-ok-flip", r"\.is_ok\(\)", ".is_err()"),
    ("rust-is-err-flip", r"\.is_err\(\)", ".is_ok()"),
    ("in-to-not-in", r"\bin\b(?!\s*\(|\s*\{|\s*\[)", "not in"),
    ("not-in-to-in", r"\bnot\s+in\b", "in"),
    ("zero-to-one", r"(?<![\w.])0(?![\w.])", "1"),
    ("empty-str-flip", r'""|\'\'', '"mutant"'),
]
COMMENT = re.compile(r"^\s*(#|//|\*|/\*)")
STRING_ONLY = re.compile(r"""^\s*(['"]).*\1,?\s*$""")


def is_balanced_delimiters(code):
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}
    in_str = None
    escaped = False
    for ch in code:
        if escaped:
            escaped = False
            continue
        if ch == '\\':
            escaped = True
            continue
        if in_str:
            if ch == in_str:
                in_str = None
            continue
        if ch in ('"', "'", '`'):
            in_str = ch
            continue
        if ch in pairs.values():
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack[-1] != pairs[ch]:
                return False
            stack.pop()
    return not stack and in_str is None


def is_valid_syntax(source, lang="py"):
    if lang == "py":
        try:
            ast.parse(source)
            return True
        except (SyntaxError, ValueError):
            return False
    return is_balanced_delimiters(source)


def detect_lang(filename):
    ext = Path(filename).suffix.lower()
    if ext == ".py":
        return "py"
    if ext in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"):
        return "js"
    if ext == ".go":
        return "go"
    if ext == ".rs":
        return "rs"
    return "other"


def generate(source, limit, is_py=False, lang=None, only=None):
    """Unique mutations, one per (line, resulting text): two operators that produce the same line
    (zero-to-one and int-off-by-one on `0`) are one mutant, and a Python mutant whose syntax tree
    equals the original is no mutant at all. `only`: the line numbers that may be mutated."""
    if lang is None:
        lang = "py" if is_py else "other"
    lines = source.splitlines()
    original_tree = ast.dump(ast.parse(source)) if lang == "py" and is_valid_syntax(source, "py") else None
    out, seen = [], set()
    for no, line in enumerate(lines, 1):
        if (only is not None and no not in only) or not line.strip() or COMMENT.match(line) \
                or STRING_ONLY.match(line) or source.count(line) != 1:
            continue
        for name, pattern, repl in OPERATORS:
            mutated = re.sub(pattern, repl, line, count=1)
            if mutated == line or (no, mutated) in seen:
                continue
            if lang in ("py", "js", "go", "rs"):
                test_lines = list(lines)
                test_lines[no - 1] = mutated
                text = "\n".join(test_lines)
                if not is_valid_syntax(text, lang=lang):
                    continue
                if original_tree is not None and ast.dump(ast.parse(text)) == original_tree:
                    continue
            seen.add((no, mutated))
            out.append({"line": no, "operator": name, "before": line, "after": mutated})
            if len(out) >= limit:
                return out
    return out


PROBES = {"py": 'raise SystemExit("verify-probe: line reached")',
          "js": 'throw new Error("verify-probe: line reached");',
          "go": 'panic("verify-probe: line reached")',
          "rs": 'panic!("verify-probe: line reached");'}
NOT_A_STATEMENT = re.compile(r"(\}|\)|\]|\.|&&|\|\||\?|:|else\b|case\b|default\b|catch\b|finally\b)")


def probe(source, no, lang):
    """The source with an abort inserted before line `no`, or None where that cannot be done safely.
    If every check still passes with the probe in, no check executes that line."""
    stmt = PROBES.get(lang)
    if not stmt:
        return None
    lines = source.splitlines()
    line = lines[no - 1]
    probed = lines[:no - 1] + [line[:len(line) - len(line.lstrip())] + stmt] + lines[no - 1:]
    text = "\n".join(probed) + ("\n" if source.endswith("\n") else "")
    if lang == "py":
        return text if is_valid_syntax(text, "py") else None
    prev = next((l.strip() for l in reversed(lines[:no - 1]) if l.strip()), "")
    if not prev.endswith((";", "{", "}")) or NOT_A_STATEMENT.match(line.lstrip()):
        return None
    return text if is_balanced_delimiters(text) else None


class LaneError(Exception):
    pass


class Lane:
    """One scratch copy of the repo. trial() writes a source into one target, runs the feature's
    checks, restores the target and recopies the lane if the checks left anything else changed."""

    def __init__(self, v, repo, path, feat, frozen, recipe, timeout, sources):
        self.v, self.repo, self.path, self.feat, self.frozen = v, repo, Path(path), feat, frozen
        self.recipe, self.timeout, self.sources = recipe, timeout, sources  # {relative path: text}
        self.copies, self.sig = 0, None

    def fresh(self):
        from challenge import copy_repo
        if self.path.exists():
            shutil.rmtree(self.path)
        copy_repo(self.v, self.repo, self.path)
        self.copies += 1
        rows, intact = self.trial(None)
        if not intact or not rows or not all(row and row["ok"] for _, _, row in rows):
            raise LaneError("original checks must pass with stable checks first")
        self.sig = self.v.tree_sig(str(self.path))

    def run_rows(self):
        v, lane = self.v, str(self.path)
        if self.recipe:  # the Run recipe starts the app: run the whole recipe, one lane only
            with contextlib.redirect_stdout(io.StringIO()):
                v.cmd_run(lane, None, self.timeout, False, use_cache=False, judge_reach=False)
            checks = v.load_state(lane).get("checks", {})
            return [(k, c, checks.get(f"{self.feat['name']}|{c}")) for k, c in self.feat["checks"]]
        rows = []
        for kind, cmd in self.feat["checks"]:
            ok, code, out, _, _ = v.attempt(cmd, lane, self.timeout, 1)
            rows.append((kind, cmd, {"ok": ok, "exit": code, "output": out[-8000:]}))
        return rows

    def trial(self, wrong):
        """(rows, intact) for wrong = (relative path, text) in place of that target; None runs the
        original."""
        rel, text = wrong if wrong is not None else (None, None)
        if rel is not None:
            (self.path / rel).write_text(text, encoding="utf-8")
        try:
            rows = self.run_rows()
            intact = self.v.check_hashes(str(self.path)) == self.frozen and all(
                (self.path / r).read_text(encoding="utf-8") == (text if r == rel else src)
                for r, src in self.sources.items())
        finally:
            if rel is not None:
                (self.path / rel).write_text(self.sources[rel], encoding="utf-8")
        if wrong is not None and self.v.tree_sig(str(self.path)) != self.sig:
            self.fresh()
        return rows, intact


def run_lanes(lanes, tasks, do):
    """do(lane, task) for every task, spread over the lanes; ({index: result}, {lane: error})."""
    todo = queue.Queue()
    for i in range(len(tasks)):
        todo.put(i)
    results, errors = {}, {}

    def work(lane):
        try:
            if lane.sig is None:
                lane.fresh()
            while True:
                try:
                    i = todo.get_nowait()
                except queue.Empty:
                    return
                results[i] = do(lane, tasks[i])
        except (LaneError, OSError, ValueError) as exc:
            errors[lane] = str(exc)

    if len(lanes) == 1:
        work(lanes[0])
    else:
        with ThreadPoolExecutor(max_workers=len(lanes)) as pool:
            list(pool.map(work, lanes))
    return results, errors


def git_lines(repo, *args):
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode:
        raise ValueError(f"git {' '.join(args)} failed: {p.stderr.strip() or p.returncode}")
    return [line for line in p.stdout.splitlines() if line.strip()]


HUNK = re.compile(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@")


def changed_lines(repo, ref, rel):
    """Line numbers of `rel` (repo-relative) added or changed since `ref`; None (every line) if untracked."""
    if not git_lines(repo, "ls-files", "--", rel):
        return None
    lines = set()
    for line in git_lines(repo, "diff", "-U0", "--no-color", "--no-ext-diff", ref, "--", rel):
        m = HUNK.match(line)
        if m:
            start, count = int(m.group(1)), int(m.group(2) or 1)
            lines.update(range(start, start + count))
    return lines


def changed_files(v, repo, ref, frozen):
    """Repo-relative product files changed since `ref` or untracked, in a language we can mutate."""
    from challenge import mutable_target
    names = set(git_lines(repo, "diff", "--name-only", "--relative", ref))
    names |= set(git_lines(repo, "ls-files", "--others", "--exclude-standard"))
    out = []
    for name in sorted(names):
        try:
            mutable_target(v, repo, frozen, name)
        except (OSError, ValueError):
            continue
        if detect_lang(name) != "other":
            out.append(name)
    return out


def path_files(v, repo, frozen, feat):
    """The mutable product files under a feature's `path:` entries, in recipe order."""
    from challenge import mutable_target
    out = []
    for p in feat.get("paths", []):
        p = p.strip().rstrip("/").replace("\\", "/")
        full = os.path.join(repo, p)
        if os.path.isfile(full):
            found = [p]
        elif os.path.isdir(full):
            found = []
            for here, dirs, files in os.walk(full):
                dirs[:] = sorted(d for d in dirs if d not in v.SKIP_DIRS and not v.is_state_file(d))
                found += [os.path.relpath(os.path.join(here, f), repo).replace("\\", "/") for f in sorted(files)]
        else:
            continue
        for rel in found:
            if rel in out or detect_lang(rel) == "other":
                continue
            try:
                mutable_target(v, repo, frozen, rel)
            except (OSError, ValueError):
                continue
            out.append(rel)
    return out


def cmd_auto(v, repo, feature, rel_file, timeout, limit, as_json, jobs=1, diff=None, found=None):
    """found: a list that gets each decided mutation (caught, survived or uncovered), for a caller
    that reports them."""
    from challenge import prepare, mutable_target, judge
    root = Path(repo).resolve()
    try:
        if timeout <= 0 or jobs < 1:
            raise ValueError("timeout and jobs must be positive")
        frozen, feat, recipe = prepare(v, repo, feature, need_signal=False)
        if rel_file:
            names = [rel_file]
        elif diff:
            names = changed_files(v, repo, diff, frozen)
            if not names:
                raise ValueError(f"no changed product file since {diff}")
        else:
            names = path_files(v, repo, frozen, feat)
            if not names:
                raise ValueError(f"feature {feature!r} has no `path:` naming a product file; "
                                 "pass the FILE to mutate or --diff")
        sources, candidates = {}, []
        for name in names:
            target = mutable_target(v, repo, frozen, name)
            rel = target.relative_to(root).as_posix()
            sources[rel] = target.read_text(encoding="utf-8")
            only = changed_lines(repo, diff, rel) if diff else None
            lang = detect_lang(rel)
            for c in generate(sources[rel], limit - len(candidates), is_py=(lang == "py"), lang=lang, only=only):
                candidates.append(dict(c, file=rel))
            if len(candidates) >= limit:
                break
    except (OSError, ValueError) as exc:
        print(f"CHALLENGE-AUTO: invalid ({exc}); score n/a")
        return 2
    if not candidates:
        since = f"changed since {diff} " if diff else ""
        print(f"CHALLENGE-AUTO: invalid (no mutable lines {since}in {', '.join(names)}); score n/a")
        return 2
    if recipe:
        jobs = 1  # one app on one port: parallel lanes would collide
    jobs = min(jobs, len(candidates))
    original_tree, original_state = v.tree_sig(repo), v.load_state(repo)

    def mutant(lane, c):
        rows, intact = lane.trial((c["file"], sources[c["file"]].replace(c["before"], c["after"], 1)))
        verdict, reason, _ = judge(v, feat, rows, intact)
        return dict(c, verdict=verdict, reason=reason)

    def probed(rel, line):
        return probe(sources[rel], line, detect_lang(rel))

    def reached(lane, spot):
        rows, intact = lane.trial((spot[0], probed(*spot)))
        return not (intact and all(row and row["ok"] for _, _, row in rows))

    with tempfile.TemporaryDirectory(prefix="verify-auto-") as tmp:
        lanes = [Lane(v, repo, Path(tmp, f"lane{i}"), feat, frozen, recipe, timeout, sources)
                 for i in range(jobs)]
        done, errors = run_lanes(lanes, candidates, mutant)
        lane_error = next(iter(errors.values()), "lane stopped before this mutation")
        results = [done.get(i) or dict(c, verdict="inconclusive", reason=lane_error)
                   for i, c in enumerate(candidates)]
        # A survivor may be a weak check or a line no check runs; a probe that aborts there tells which.
        spots = sorted({(r["file"], r["line"]) for r in results
                        if r["verdict"] == "survived" and probed(r["file"], r["line"])})
        live = [lane for lane in lanes if lane not in errors][:len(spots)]
        if live:
            hit, _ = run_lanes(live, spots, reached)
            unreached = {spot for i, spot in enumerate(spots) if hit.get(i) is False}
            for r in results:
                if r["verdict"] == "survived" and (r["file"], r["line"]) in unreached:
                    r.update(verdict="uncovered",
                             reason=f"breaking {r['before'].strip()} (e.g. -> {r['after'].strip()}) still passed: "
                                    "no check reaches this line (a probe that aborts there still passes)")
        copies = sum(lane.copies for lane in lanes)

    # Receipts other agents add meanwhile are additive evidence; anything else changing is not.
    def settled(state):
        return {k: val for k, val in state.items() if k != "failures"}

    if v.tree_sig(repo) != original_tree or settled(v.load_state(repo)) != settled(original_state):
        print("CHALLENGE-AUTO: inconclusive (source files or verification state changed during challenge); score n/a")
        return 2
    caught = sum(r["verdict"] == "caught" for r in results)
    if found is not None:
        found += [dict(r, feature=feature) for r in results if r["verdict"] in ("caught", "survived", "uncovered")]
    survived = [r for r in results if r["verdict"] == "survived"]
    uncovered = [r for r in results if r["verdict"] == "uncovered"]
    decided = caught + len(survived) + len(uncovered)
    score = round(caught / decided, 3) if decided else None
    summary = {"feature": feature, "file": rel_file, "files": sorted(sources), "diff": diff,
               "generated": len(candidates), "run": len(results),
               "caught": caught, "survived": len(survived), "uncovered": len(uncovered),
               "inconclusive": len(results) - decided, "score": score, "jobs": jobs, "copies": copies,
               "results": results}
    if as_json:
        print(json.dumps(summary, indent=2))
    else:
        shown = "n/a" if score is None else f"{score:.0%}"
        scope = f" (lines changed since {diff})" if diff else ""
        if not feat["signals"]:
            print("note  no fail-signal declared: any failing check counts as caught. Declare one to "
                  "tell a real rejection from a crash.")
        print(f"CHALLENGE-AUTO: {caught}/{decided} caught (score {shown}), {len(uncovered)} uncovered, "
              f"{summary['inconclusive']} inconclusive, feature {feature!r}, "
              f"file {', '.join(sorted(sources))}{scope}")

        def at(r):
            return f"line {r['line']}" if len(sources) == 1 else f"{r['file']}:{r['line']}"
        for r in survived:
            print(f"  SURVIVED {at(r)} {r['operator']}: {r['before'].strip()} -> {r['after'].strip()} (check still passed)")
        for r in uncovered:
            print(f"  UNCOVERED {at(r)} {r['operator']}: breaking {r['before'].strip()} (-> {r['after'].strip()}) still passed: no check reaches the line")
        for r in results:
            if r["verdict"] == "inconclusive":
                print(f"  INCONCLUSIVE {at(r)} {r['operator']}: {r['reason']}")
        print("Survivors are leads, not verdicts: judge each as a real gap or an equivalent mutation. "
              "Uncovered lines need a check that reaches them. No fail-proof receipts were recorded.")
    if decided == 0:
        return 2
    return 1 if survived or uncovered else 0
