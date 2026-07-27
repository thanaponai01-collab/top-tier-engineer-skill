#!/usr/bin/env python3
"""
structure_opacity — how much of a file did the analyzer never enter, and was the
part it skipped actually code?

THE PRINCIPLE (PROTOCOL §10 rule 5)
-----------------------------------
A measurement's denominator is part of the measurement. Every structural analyzer
enters some of the source and skips the rest; the skipped part is not clean, it is
UNMEASURED — and in a report that does not state coverage, unmeasured reads exactly
like clean. That is how an entire second language can hide inside one string literal
while every complexity, nesting, and function-length number in the report says zero —
and every one of those zeros is correct.

The first version of this detector matched markers — `<script`, `function `,
`SELECT`. That is hard-coded knowledge of four languages, so it is wrong by
construction: it dates, and the fifth language walks straight past it (suite Law 6,
constrain process never intelligence). This module replaces the vocabulary question
with two questions that have the same answer in every language, including one
invented tomorrow:

  1. OPACITY — which lines does the file's own lexer classify as string/comment
     rather than code? That is not a heuristic; it is the language's own tokenizer
     telling you exactly where the analysis stopped. No marker list can be wrong
     about it because no marker list is consulted.

  2. SHAPE — is the opaque region structured like code, like data, or like prose?
     Answerable from content-free statistics, because CODE IS A TREE OF VARIED
     STATEMENTS while prose is a uniform stream and tabular data is uniform rows.
     Which statistics, and why the obvious first choices were wrong, is documented
     where they are implemented (section 2 below) rather than restated here.

Opaque + structured = code no linter, test harness, or complexity metric can reach —
untestable by construction rather than by omission.

WHAT THIS DELIBERATELY DOES NOT DO
----------------------------------
It does not name the language. Naming requires vocabulary, vocabulary dates, and the
name is decoration: the finding ("1,400 lines of structured code your tools cannot
see") is identical whether it turns out to be JSX, Handlebars, or something with no
name yet. `looks_like()` offers a non-load-bearing hint for the human report and is
never consulted when deciding whether to flag.

EXTENDING TO ANOTHER LANGUAGE
-----------------------------
Add a lexer to `LEXERS`. It needs one capability: report which source lines are
string-or-comment. Everything downstream is language-independent and needs no edit.
A language with no lexer here is reported as coverage UNKNOWN, never as clean —
silence about a region must never be presented as a result for that region.
"""
import io
import os
import re
import tokenize
from collections import defaultdict


def add_scanner_coverage(coverage, paths, n_scanned, admitted_exts, skip_dirs):
    """Attach the scanner's own denominator: admitted files vs files on disk."""
    unscanned = unscanned_census(paths, admitted_exts, skip_dirs)
    n_disk = n_scanned + unscanned["files"]
    coverage["files_scanned"] = n_scanned
    coverage["files_on_disk"] = n_disk
    coverage["pct_files_scanned"] = (round(100 * n_scanned / n_disk, 1)
                                     if n_disk else 0.0)
    coverage["unscanned"] = unscanned


def print_coverage(c):
    """The coverage block — printed ABOVE the headline verdict, never after it.

    A director must not be able to read a green result without the fraction it was
    measured over (§10 rule 5, and Law 4, director-readable output). Rendering lives
    beside the measurement because the two must not drift: a coverage number nobody
    prints is the same defect as one nobody measures.
    """
    print(f"Coverage: {c['code_lines']:,} code lines · {c['pct_entered']}% actually "
          f"entered by a parser · {c['opaque']:,} opaque\n          (inside string "
          f"literals) · {c['shallow']:,} shallow (no parser for that language here) · "
          f"{c['documented']:,} docs")
    if c["pct_entered"] < 100:
        print("          Everything below was measured over the entered portion ONLY. The")
        print("          rest is unmeasured, which is not the same as clean.")
    u = c.get("unscanned") or {"files": 0, "bytes": 0, "by_ext": []}
    print(f"          Files: {c.get('files_scanned', 0)} of "
          f"{c.get('files_on_disk', 0)} on disk admitted by the scanner "
          f"({c.get('pct_files_scanned', 0.0)}%).")
    if u["files"]:
        exts = ", ".join(f"{e}×{n}" for e, n in u["by_ext"][:6])
        print(f"  ⚠️  UNKNOWN — {u['files']} file(s), {u['bytes']:,} bytes were never "
              f"opened by this gate\n      (extension not in its admission list): {exts}"
              + (" …" if len(u["by_ext"]) > 6 else ""))
        print("      These are UNMEASURED, not clean. Every verdict below is scoped to "
              "the\n      admitted files only.")


def unscanned_census(paths, admitted_exts, skip_dirs):
    """Blind-spot class 2: files on disk the SCANNER never admitted.

    This module's other half measures class 1 — what the *parser* skipped inside a file
    it opened. This measures the layer above: what never got opened at all, because its
    extension was not in the caller's admission list. Both are PROTOCOL §10 rule 5, and
    until this existed the class-2 region contributed zero to every signal AND zero to
    the coverage denominator, so the reported percentage was a fraction of an
    already-filtered population — unmeasured rendering as clean, one level up.

    The admission list is a parameter, never a constant here: this census owns no
    vocabulary of its own (§10 rule 6). It reports whatever the caller's list left out,
    whatever that turns out to be, so it cannot date the way a marker list does.
    """
    n_files, n_bytes, by_ext = 0, 0, defaultdict(int)
    for p in paths:
        walk = ([(os.path.dirname(p) or ".", [], [os.path.basename(p)])]
                if os.path.isfile(p) else os.walk(p))
        for root, dirs, files in walk:
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for f in files:
                ext = os.path.splitext(f)[1]
                if ext in admitted_exts:
                    continue
                n_files += 1
                by_ext[ext.lower() or "(no extension)"] += 1
                try:
                    n_bytes += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
    return {"files": n_files, "bytes": n_bytes,
            "by_ext": sorted(by_ext.items(), key=lambda kv: -kv[1])}

# ---- 1. OPACITY: ask the language's own lexer where the analysis stopped --------


def _python_doc_lines(src):
    """Lines belonging to a docstring — Python's own declared documentation slot.

    Documentation is not a blind spot; it is prose in the place prose belongs, and
    counting it as unmeasured source makes every well-documented file look opaque.
    (Measured: the suite's own tools produced three false positives on their module
    docstrings before this exclusion existed.) Note this is a *structural* fact the
    language defines — first statement of a module/class/function — not a vocabulary
    guess about what the text says, so it costs none of the generality above.
    """
    import ast
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    lines = set()
    for n in ast.walk(tree):
        body = getattr(n, "body", None)
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) \
                and body and isinstance(body[0], ast.Expr) \
                and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            c = body[0].value
            lines.update(range(c.lineno, (c.end_lineno or c.lineno) + 1))
    return lines


def python_opaque_lines(src):
    """(opaque, documented) line numbers, 1-based, from CPython's own lexer.

    `opaque` — lines that are nothing but a *value* string: the analyzer stopped at
    them and what is inside is unknown. This is the blind spot.
    `documented` — docstring and comment lines: declared prose, excluded from the
    coverage denominator entirely rather than counted as unmeasured source.

    Using `tokenize` rather than a delimiter heuristic makes this exact for f-strings,
    implicit concatenation, raw strings, and nested quotes alike. Returns None when
    the file cannot be tokenized — report as UNKNOWN, never as clean.
    """
    strings, comments, code = set(), set(), set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.STRING:
                target = strings
            elif tok.type == tokenize.COMMENT:
                target = comments
            elif tok.type in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                              tokenize.DEDENT, tokenize.ENDMARKER):
                continue
            else:
                target = code
            target.update(range(tok.start[0], tok.end[0] + 1))
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        return None
    # A line holding both a string and real code (`x = "short"`) is not opaque: the
    # analyzer did enter it. Only lines that are nothing but string/comment count.
    docs = (_python_doc_lines(src) | comments) - code
    return (strings - code - docs), docs


LEXERS = {".py": python_opaque_lines}


def contiguous_spans(lines, minimum=1):
    """Maximal runs of consecutive line numbers, as [(start, end), …]."""
    spans, run_start, prev = [], None, None
    for n in sorted(lines):
        if prev is None or n != prev + 1:
            if run_start is not None and prev - run_start + 1 >= minimum:
                spans.append((run_start, prev))
            run_start = n
        prev = n
    if run_start is not None and prev - run_start + 1 >= minimum:
        spans.append((run_start, prev))
    return spans


# ---- 2. SHAPE: is the opaque region code, data, or prose? -----------------------
# The first cut of this scored bracket-nesting depth, `;`/`}` line terminators, and
# symbol density. Measured against fixtures, those three describe the C FAMILY, not
# code: Lua scored 1/4 and was classified as prose because it nests with do/end and
# ends lines in words. That is the same vocabulary bug as the marker list, one level
# up and harder to see — a "content-free" statistic that silently assumed a syntax.
#
# What survived measurement is what is true of code in every syntax family: CODE IS A
# TREE OF VARIED STATEMENTS. Prose is a uniform stream; tabular data is uniform rows;
# only code is both nested and irregular. Measured separations across prose (English,
# wrapped), flat data (CSV, JSON), and code (HTML/CSS/JS, Lua, Python, SQL, and an
# invented syntax matching no marker anywhere in this suite):
#
#     signal            prose        flat data     code
#     indent_levels     1            1–2           3–4
#     length_cv         0.005–0.026  0.021–0.132   0.243–0.774
#
# Both separate every fixture with a wide margin, and neither knows a language.
# Thresholds are illustrative defaults calibrated in tools/test_tools.py, not doctrine.
import statistics

MINIFIED_LINE = 500     # one machine-generated line: a tree flattened, still code


def shape_stats(text):
    """Content-free structural statistics for any text in any language."""
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return {"indent_levels": 0, "length_cv": 0.0, "max_line": 0,
                "score": 0, "lines": 0}

    lengths = [len(l.strip()) for l in lines]
    mean = statistics.mean(lengths)
    length_cv = statistics.pstdev(lengths) / mean if mean else 0.0
    indent_levels = len({len(l) - len(l.lstrip()) for l in lines})
    max_line = max(lengths)

    criteria = (indent_levels >= 3,   # nested: a tree, not a stream or a table
                length_cv >= 0.2)     # irregular: statements differ, unlike wrapped
                                      # prose or fixed-width rows
    return {"indent_levels": indent_levels, "length_cv": round(length_cv, 4),
            "max_line": max_line, "score": sum(criteria), "lines": len(lines)}


def is_code_shaped(stats):
    """Both tree-signals, or one unmistakably machine-generated line.

    Requiring BOTH keeps flat data out (JSON hits indentation but never irregularity).
    The minified clause is the one shape that defeats both by construction — a bundle
    on a single 50KB line is a tree that was flattened, and it is still code nothing
    can test.
    """
    return stats["score"] >= 2 or stats["max_line"] >= MINIFIED_LINE


# ---- 3. A HINT ONLY. Never consulted when deciding to flag. ---------------------
_HINTS = {
    "markup": re.compile(r"<\w+[^>]*>|</\w+>|<!doctype", re.I),
    "css":    re.compile(r"^\s*[.#]?[\w-]+[^\n{]*\{[^}]*:[^}]*;", re.M),
    "js":     re.compile(r"\bfunction\b|=>|\bconst\b|\bdocument\.|\bvar\b"),
    "sql":    re.compile(r"\bSELECT\b[^\n]{0,200}?\bFROM\b", re.I),
    "shell":  re.compile(r"^\s*(?:#!/|\$\(|echo |set -e)", re.M),
}


def looks_like(text):
    """Best-guess label for the human report. Decoration, never a trigger.

    The finding is identical whether this returns 'js/markup' or nothing at all, which
    is the point: a detector that needed this to work would inherit its blind spots.
    """
    return sorted(n for n, rx in _HINTS.items() if rx.search(text)) or ["unrecognized"]


# ---- 4. The composed measurement -----------------------------------------------
def measure(path, src, min_span):
    """Opacity + shape for one file.

    Returns {supported, total, opaque, documented, spans:[…]}. `spans` holds only runs
    at or over `min_span` that are also code-shaped — the reportable blind spots.
    `opaque` counts every value-string line regardless, because coverage is reported
    over all of it, not only over the parts that tripped a threshold.
    """
    ext = "." + path.rsplit(".", 1)[-1] if "." in path else ""
    lexer = LEXERS.get(ext)
    total = len(src.splitlines())
    blank = {"supported": False, "total": total, "opaque": 0, "documented": 0,
             "spans": []}
    if lexer is None:
        return blank

    measured = lexer(src)
    if measured is None:
        return blank
    opaque, docs = measured

    lines = src.splitlines()
    spans = []
    for start, end in contiguous_spans(opaque, minimum=min_span):
        text = "\n".join(lines[start - 1:end])
        stats = shape_stats(text)
        if is_code_shaped(stats):
            spans.append({"start": start, "end": end, "lines": end - start + 1,
                          "stats": stats, "hint": "/".join(looks_like(text))})
    return {"supported": True, "total": total, "opaque": len(opaque),
            "documented": len(docs), "spans": spans}
