"""challenge --auto: generate standard single-line mutations for one product file and run each
through the challenge runner in survey mode. The result is a mutation score for one feature.

Generated mutations are not spec-backed, so a caught one never becomes a fail-proof receipt;
a survivor is a lead for a person to judge (a real gap, or an equivalent mutation)."""
import contextlib
import io
import json
import os
import re
import tempfile
from pathlib import Path

import ast

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


def generate(source, limit, is_py=False, lang=None):
    if lang is None:
        lang = "py" if is_py else "other"
    lines = source.splitlines()
    out = []
    for no, line in enumerate(lines, 1):
        if not line.strip() or COMMENT.match(line) or STRING_ONLY.match(line) or source.count(line) != 1:
            continue
        for name, pattern, repl in OPERATORS:
            mutated = re.sub(pattern, repl, line, count=1)
            if mutated != line:
                if lang in ("py", "js", "go", "rs"):
                    test_lines = list(lines)
                    test_lines[no - 1] = mutated
                    if not is_valid_syntax("\n".join(test_lines), lang=lang):
                        continue
                out.append({"line": no, "operator": name, "before": line, "after": mutated})
                if len(out) >= limit:
                    return out
    return out


def cmd_auto(v, repo, feature, rel_file, timeout, limit, as_json):
    target = Path(repo, rel_file)
    try:
        source = target.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"CHALLENGE-AUTO: invalid ({exc})")
        return 2
    lang = detect_lang(rel_file)
    candidates = generate(source, limit, is_py=(lang == "py"), lang=lang)
    if not candidates:
        print(f"CHALLENGE-AUTO: invalid (no mutable lines in {rel_file})")
        return 2
    from challenge import cmd_challenge
    results = []
    with tempfile.TemporaryDirectory(prefix="verify-auto-") as tmp:
        for i, c in enumerate(candidates):
            spec = Path(tmp, f"m{i}.json")
            spec.write_text(json.dumps({"file": rel_file, "before": c["before"], "after": c["after"],
                                        "claim": f"auto {c['operator']} at line {c['line']}"}), encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = cmd_challenge(v, repo, feature, str(spec), timeout, record=False)
            verdict = {0: "caught", 1: "survived"}.get(code, "inconclusive")
            first = buf.getvalue().strip().splitlines()[:1]
            results.append(dict(c, verdict=verdict, reason=first[0] if first else ""))
            if verdict == "inconclusive" and "invalid" in (first[0] if first else ""):
                break  # setup error (unknown feature, frozen file): every candidate would fail the same way
    caught = sum(r["verdict"] == "caught" for r in results)
    survived = [r for r in results if r["verdict"] == "survived"]
    decided = caught + len(survived)
    score = round(caught / decided, 3) if decided else None
    summary = {"feature": feature, "file": rel_file, "generated": len(candidates), "run": len(results),
               "caught": caught, "survived": len(survived), "inconclusive": len(results) - decided,
               "score": score, "results": results}
    if as_json:
        print(json.dumps(summary, indent=2))
    else:
        shown = "n/a" if score is None else f"{score:.0%}"
        print(f"CHALLENGE-AUTO: {caught}/{decided} caught (score {shown}), "
              f"{summary['inconclusive']} inconclusive, feature {feature!r}, file {rel_file}")
        for r in survived:
            print(f"  SURVIVED line {r['line']} {r['operator']}: {r['before'].strip()} -> {r['after'].strip()}")
        for r in results:
            if r["verdict"] == "inconclusive":
                print(f"  INCONCLUSIVE line {r['line']} {r['operator']}: {r['reason']}")
        print("Survivors are leads, not verdicts: judge each as a real gap or an equivalent mutation. "
              "No fail-proof receipts were recorded.")
    if decided == 0:
        return 2
    return 1 if survived else 0
