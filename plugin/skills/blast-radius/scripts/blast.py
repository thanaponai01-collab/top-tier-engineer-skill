#!/usr/bin/env python3
"""blast.py - the mechanical side of the blast-radius skill.

A change can do what it meant and still break code it never touched: a caller passing the old
arguments, a reader of a key or column it renamed, a script reading an env var it dropped. This
lists every consumer outside the diff and will not let the change be called safe until the one
fact it is safe because of has been run, and seen failing with that fact broken:

  B --base REF          what the diff against REF changed (Python functions by AST, words it no
                        longer writes by literal name in every tracked text file) and every
                        consumer of it outside the diff; .blast/consumers.json
  B --gate [--app CMD]  check the stages, print every problem with its fix, draft the answer:
    1 list     the consumer list is current with the code
    2 account  every consumer has a verdict in .blast/verdicts.md (breaks|cleared|unknown)
    3 fact     .blast/fact.md's proof passes on a copy of the change and fails on a copy with
               its break applied (level 4); --app CMD shows the same in the running app (level 5)
  B --answer-check FILE refuse an answer whose level, verdict or `safe` the helper did not see

The level is the highest the helper saw: 1 said so, 2 cited a file:line that exists, 3 walked the
failure (a `- walk:` line through two or more such lines), 4 ran it, 5 ran the app. The product
tree is never written: proofs run in throwaway copies, and only .blast/ changes.
`B` is `python blast.py <repo>`. Stdlib only.
"""
import argparse, ast, builtins, hashlib, json, keyword, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _encoding import utf8_streams  # noqa: E402

STATE = ".blast"
CONSUMERS = f"{STATE}/consumers.json"
VERDICTS = f"{STATE}/verdicts.md"
FACT = f"{STATE}/fact.md"
LEDGER = f"{STATE}/state.json"
ANSWER = f"{STATE}/answer.md"
FILL = "[[fill"
# Folders that hold tools' state or caches, never the product: not scanned, copied or compared.
NOT_PRODUCT = {".git", "__pycache__", "node_modules", ".venv", "venv", STATE, ".verify-state",
               ".verify-state-cache", ".wire", ".features", ".release", ".evolve", ".perf", ".latent",
               ".debug", ".structure", ".threat", ".mistakes", ".formal", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
NOT_PRODUCT_FILES = {".verify-state.json"}
CLASSES = ("breaks", "cleared", "unknown")
CITED = {"breaks", "cleared"}
# Words too common to be a name a reader depends on.
COMMON = set(keyword.kwlist) | set(dir(builtins)) | {"self", "cls", "true", "false", "null", "none",
                                                      "def", "return", "the", "and", "for", "var",
                                                      "let", "const", "function", "this"}
RANK = {"removed": 0, "signature": 1, "name": 2, "behaviour": 3}
BASH = shutil.which("bash")
LEVELS = {0: "nothing said", 1: "said so", 2: "cited a file:line that exists",
          3: "walked the failure through the lines it passes", 4: "ran it", 5: "reproduced in the running app"}
VERDICTS_HEAD = """# Blast verdicts

One line per consumer outside the diff: `- <file:line>: breaks|cleared|unknown: <why>`.
`breaks` and `cleared` cite the file:line (or the library source file:line) they rest on; `unknown`
says what it depends on. A consumer outside the repo (another service, another repo):
`- outside <who>: unknown: <what it depends on>`.

"""
FACT_HELP = ("write .blast/fact.md: `- fact: <the one fact the change is safe because of>`, "
             "`- cite: <file:line>`, `- proof: `<command that fails when the fact is false>``, "
             "`- break: <file>`, `- old: `<text in it>``, `- new: `<text that makes the fact false>``")


# ---------------- the repo ----------------------------------------------------
def git(repo, *args):
    p = subprocess.run(["git", "--no-optional-locks", "-c", "core.quotePath=false", "-C", repo, *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout, p.stderr


def not_product(rel_path):
    parts = rel_path.split("/")
    return any(p in NOT_PRODUCT for p in parts[:-1]) or parts[-1] in NOT_PRODUCT_FILES


def read_bytes(repo, rel_path):
    try:
        with open(os.path.join(repo, rel_path), "rb") as fh:
            return fh.read()
    except OSError:
        return None


def read_text(repo, rel_path):
    data = read_bytes(repo, rel_path)
    return "" if data is None else data.decode("utf-8", errors="replace")


def is_text(data):
    return data is not None and len(data) < 2_000_000 and b"\0" not in data[:8192]


def product_files(repo):
    """Every tracked or untracked-but-not-ignored text file outside the tools' state folders."""
    code, out, _ = git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    files = sorted({f for f in out.split("\0") if f} if code == 0 else set())
    return [f for f in files if not not_product(f) and is_text(read_bytes(repo, f))]


def shas(repo):
    return {f: hashlib.sha256(read_bytes(repo, f)).hexdigest()[:16] for f in product_files(repo)}


def read_json(repo, rel_path, default=None):
    try:
        with open(os.path.join(repo, rel_path), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_file(repo, rel_path, text):
    path = os.path.join(repo, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def write_json(repo, rel_path, data):
    write_file(repo, rel_path, json.dumps(data, indent=1, sort_keys=True))


# ---------------- what the diff changed --------------------------------------
def parse_diff(text):
    """{path: {"new_lines": set, "removed": [line text]}} from `git diff -U0`."""
    out, path, old = {}, None, None
    for line in text.splitlines():
        line = line.rstrip("\r")
        if line.startswith("--- "):
            old = None if line == "--- /dev/null" else line[6:]
        elif line.startswith("+++ "):
            path = old if line == "+++ /dev/null" else line[6:]
            out.setdefault(path, {"new_lines": set(), "removed": []})
        elif line.startswith("@@") and path:
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
            if m:
                start, n = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
                out[path]["new_lines"].update(range(start, start + n))
        elif line.startswith("-") and path:
            out[path]["removed"].append(line[1:])
    return out


def functions(text):
    """{qualname: (line, signature, whole)} for top-level functions and methods of top-level classes."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return {}
    out = {}
    for node in tree.body:
        items = [(node.name, node)] if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else []
        if isinstance(node, ast.ClassDef):
            items = [(f"{node.name}.{i.name}", i) for i in node.body
                     if isinstance(i, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for name, fn in items:
            out[name] = (fn.lineno, ast.dump(fn.args), ast.dump(fn))
    return out


def words(text):
    counts = {}
    for w in re.findall(r"[A-Za-z_]\w*", text):
        counts[w] = counts.get(w, 0) + 1
    return counts


def what_changed(repo, base):
    """(changed files {path: new-side changed lines}, symbols [(name, kind, file, line)], names [word])."""
    code, out, err = git(repo, "diff", "-U0", "--no-color", "--no-ext-diff", "--no-renames", base, "--")
    if code != 0:
        return None, err.strip().splitlines()[-1:] or [f"git diff {base} failed"], None
    diff = parse_diff(out)
    _, untracked, _ = git(repo, "ls-files", "-z", "--others", "--exclude-standard")
    for f in (u for u in untracked.split("\0") if u):
        n = len(read_text(repo, f).splitlines())
        diff.setdefault(f, {"new_lines": set(range(1, n + 1)), "removed": []})
    diff = {f: d for f, d in diff.items() if not not_product(f)}
    symbols, names = [], set()
    for f, d in sorted(diff.items()):
        _c, old_text, _e = git(repo, "show", f"{base}:{f}")
        old_text = old_text if _c == 0 else ""
        new_text = read_text(repo, f)
        if f.endswith(".py"):
            old_fns, new_fns = functions(old_text), functions(new_text)
            for q, (line, sig, whole) in sorted(old_fns.items()):
                if q not in new_fns:
                    symbols.append((q, "removed", f, line))
                elif new_fns[q][1] != sig:
                    symbols.append((q, "signature", f, new_fns[q][0]))
                elif new_fns[q][2] != whole:
                    symbols.append((q, "behaviour", f, new_fns[q][0]))
        old_w, new_w = words(old_text), words(new_text)
        for w in words("\n".join(d["removed"])):
            if len(w) >= 3 and w.lower() not in COMMON and w not in COMMON and old_w.get(w, 0) > new_w.get(w, 0):
                names.add(w)
    return {f: d["new_lines"] for f, d in diff.items()}, symbols, sorted(names)


def find_consumers(repo, changed, symbols, names):
    """[{site, file, line, what, text, rank}] for every use of a changed thing outside the diff."""
    by_sym = {}
    for q, kind, _f, _l in symbols:
        by_sym.setdefault(q.split(".")[-1], []).append(f"{q} ({kind})")
    word = re.compile(r"(?<!\w)(" + "|".join(map(re.escape, sorted(names, key=len, reverse=True))) + r")(?!\w)") \
        if names else None
    hits = {}

    def hit(f, line, what, rank):
        if line in changed.get(f, ()):
            return
        h = hits.setdefault((f, line), {"what": [], "rank": rank})
        h["rank"] = min(h["rank"], rank)
        for w in what:
            if w not in h["what"]:
                h["what"].append(w)

    for f in product_files(repo):
        text = read_text(repo, f)
        tree = None
        if f.endswith(".py"):
            try:
                tree = ast.parse(text)
            except (SyntaxError, ValueError):
                tree = None
        if tree is None:   # any other text file, or Python that will not parse: by literal name
            for i, ln in enumerate(text.splitlines(), 1):
                found = sorted(set(word.findall(ln))) if word else []
                if found:
                    hit(f, i, [f"`{w}` (name)" for w in found], RANK["name"])
            continue
        for node in ast.walk(tree):
            line = getattr(node, "lineno", None)
            ident = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else None
            if ident in by_sym:
                hit(f, line, by_sym[ident], min(RANK[w.rsplit("(", 1)[1][:-1]] for w in by_sym[ident]))
            if not word:
                continue
            found = []
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                found = word.findall(node.value)
            elif ident is not None and isinstance(node, ast.Attribute) and word.fullmatch(ident):
                found = [ident]
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                found = [a.name.split(".")[-1] for a in node.names if word.fullmatch(a.name.split(".")[-1])]
            if found:
                hit(f, line, [f"`{w}` (name)" for w in sorted(set(found))], RANK["name"])
    out = []
    for (f, line), h in hits.items():
        lines = read_text(repo, f).splitlines()
        text = lines[line - 1].strip() if 0 < line <= len(lines) else ""
        out.append({"site": f"{f}:{line}", "file": f, "line": line, "what": h["what"],
                    "text": text[:120], "rank": h["rank"]})
    return sorted(out, key=lambda c: (c["rank"], c["file"], c["line"]))


def list_consumers(repo, base):
    code, _, _ = git(repo, "rev-parse", "--verify", f"{base}^{{commit}}")
    if code != 0:
        print(f"BLAST: `{base}` is not a commit in {repo}. blast.py reads the change as `git diff <base>`: "
              "commit the code as it was before the change, then B --base <that commit>")
        return 2
    changed, symbols, names = what_changed(repo, base)
    if changed is None:
        print(f"BLAST: git diff {base} failed: {symbols[0] if symbols else ''}")
        return 2
    found = find_consumers(repo, changed, symbols, names)
    write_json(repo, CONSUMERS, {"base": base, "changed": sorted(changed), "consumers": found,
                                 "names": names, "shas": shas(repo),
                                 "symbols": [list(s) for s in symbols]})
    print(f"BLAST: base {base}, {len(changed)} file(s) changed: {', '.join(sorted(changed)[:8])}"
          + (" ..." if len(changed) > 8 else ""))
    for q, kind, f, line in symbols:
        print(f"- changed: {q} ({kind}) at {f}:{line}")
    if names:
        print("- words the diff no longer writes as often (searched in every text file): " + ", ".join(names[:30]))
    print(f"Consumers outside the diff ({len(found)}):")
    for c in found:
        print(f"- {c['site']}  {', '.join(c['what'])}  {c['text']}")
    print("next: B --gate (it drafts a verdict slot for each in .blast/verdicts.md)")
    return 0


# ---------------- verdicts ----------------------------------------------------
VERDICT_LINE = re.compile(r"^- (?P<who>outside [^:]+|.+?:\d+): (?P<cls>[\w-]+|\[\[fill[^\]]*\]\]):\s*(?P<why>.*)$")
CITE = re.compile(r"((?:[A-Za-z]:)?[\w./\\-]+\.\w+):(\d+)")


def read_verdicts(repo):
    """({who: (class, why)}, [unfilled who])."""
    verdicts, unfilled = {}, []
    for line in read_text(repo, VERDICTS).splitlines():
        m = VERDICT_LINE.match(line.strip())
        if not m:
            continue
        who = m.group("who").strip().strip("`")
        if FILL in line:
            unfilled.append(who)
        else:
            verdicts[who] = (m.group("cls"), m.group("why").strip())
    return verdicts, unfilled


def cite_ok(repo, path, line):
    """None if path:line names a line that exists (in the repo, or a library file by absolute path)."""
    p = path.replace("\\", "/")
    full = p if os.path.isabs(p) else os.path.join(repo, p)
    try:
        with open(full, encoding="utf-8", errors="replace") as fh:
            n = len(fh.read().splitlines())
    except OSError:
        return f"cites {path}, which is not a file here"
    if int(line) < 1 or int(line) > n:
        return f"cites {path}:{line}, past the end of the file"
    return None


def verdict_problem(repo, cls, why):
    if cls not in CLASSES:
        return f"class `{cls}` is not one of {', '.join(CLASSES)}"
    if len(why) < 8:
        return "says no why" + (": name what it depends on" if cls == "unknown" else "")
    if cls in CITED:
        cites = CITE.findall(why)
        if not cites:
            return f"`{cls}` needs the file:line or library source it rests on. Add it to the line in {VERDICTS}"
        for path, line in cites:
            bad = cite_ok(repo, path, line)
            if bad:
                return bad + f". Point the line in {VERDICTS} at one that exists"
    return None


# ---------------- the safety fact ---------------------------------------------
def read_fact(repo):
    """{field: value} from .blast/fact.md (`- field: value`; a backticked value loses its backticks)."""
    out = {}
    for line in read_text(repo, FACT).splitlines():
        m = re.match(r"^\s*-\s*(fact|cite|walk|proof|break|old|new):\s*(.*?)\s*$", line)
        if m and m.group(1) not in out:
            v = m.group(2)
            if m.group(1) in ("proof", "old", "new") and len(v) >= 2 and v.startswith("`") and v.endswith("`"):
                v = v[1:-1]
            out[m.group(1)] = v
    return out


def copy_tree(repo, dest):
    def ignore(d, names):
        return [n for n in names if n in NOT_PRODUCT or n in NOT_PRODUCT_FILES or n.endswith(".pyc")]
    shutil.copytree(repo, dest, ignore=ignore)


def run_both(repo, cmd, brk, timeout):
    """{"change": (exit, last line), "broken": (exit, last line)}: cmd on a copy of the change, then on
    a copy with the break applied. The repo is never written."""
    out = {}
    tmp = tempfile.mkdtemp(prefix="blast-")
    try:
        for side in ("change", "broken"):
            copy = os.path.join(tmp, side)
            copy_tree(repo, copy)
            if side == "broken":
                p = os.path.join(copy, *brk["break"].split("/"))
                with open(p, encoding="utf-8", newline="") as fh:
                    text = fh.read()
                with open(p, "w", encoding="utf-8", newline="") as fh:
                    fh.write(text.replace(brk["old"], brk["new"], 1))
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            # The agent writes commands in the shell it uses (`VAR=x cmd`, `&&`), so prefer bash.
            argv = [BASH, "-c", cmd] if BASH else cmd
            try:
                r = subprocess.run(argv, cwd=copy, shell=not BASH, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=timeout, env=env)
                tail = [ln for ln in ((r.stdout or "") + (r.stderr or "")).replace(copy, "<repo>").splitlines()
                        if ln.strip()]
                out[side] = (r.returncode, tail[-1][:160] if tail else "")
            except subprocess.TimeoutExpired:
                out[side] = ("timeout", "timed out")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def fact_level(repo, fact, app, timeout):
    """(level, problems, runs): the highest rung of the ladder the helper itself saw."""
    problems, runs = [], {}
    if not fact.get("fact"):
        return 0, [f"no safety fact: {FACT_HELP}"], runs
    level = 1
    cited = [c for k in ("fact", "cite") for c in CITE.findall(fact.get(k, ""))]
    if cited and all(cite_ok(repo, *c) is None for c in cited):
        level = 2
    elif cited:
        problems += [f"fact: {cite_ok(repo, *c)}" for c in cited if cite_ok(repo, *c)]
    else:
        problems.append("the fact cites no file:line: add `- cite: <file:line>` naming the line it rests on")
    walk = CITE.findall(fact.get("walk", ""))
    if level == 2 and len(walk) >= 2 and all(cite_ok(repo, *c) is None for c in walk):
        level = 3
    for k in ("proof", "break", "old", "new"):
        if not fact.get(k):
            problems.append(f"no `- {k}:` in {FACT}: " + {
                "proof": "a command that fails when the fact is false, run on a throwaway copy",
                "break": "the one file the break edits",
                "old": "the exact text in that file the break replaces (one line, in backticks)",
                "new": "the text that makes the fact false (in backticks)"}[k])
    brk_ok = all(fact.get(k) for k in ("proof", "break", "old", "new"))
    if fact.get("break"):
        f = fact["break"].strip("`").replace("\\", "/")
        fact["break"] = f
        text = read_text(repo, f) if not not_product(f) else ""
        if not text:
            problems.append(f"the break's file {f} is not a product file in the repo")
            brk_ok = False
        elif fact.get("old"):
            n = text.count(fact["old"])
            if n != 1:
                problems.append(f"the break's old text `{fact['old']}` is " + ("not in" if not n else f"in {n} places of")
                                + f" {f}. Copy one line from the file exactly, enough to be unique")
                brk_ok = False
    if not brk_ok:
        return level, problems, runs
    for label, cmd in (("proof", fact["proof"]), ("app", app)):
        if not cmd:
            continue
        r = runs[label] = run_both(repo, cmd, fact, timeout)
        ok = True
        if r["change"][0] != 0:
            problems.append(f"the {label} `{cmd}` fails on the change itself (exit {r['change'][0]}: "
                            f"{r['change'][1]}). Fix the command or the change")
            ok = False
        if r["broken"][0] == 0:
            problems.append(f"the {label} `{cmd}` passes with the break applied: it cannot fail. Make it check "
                            f"the fact itself, so that {fact['break']} `{fact['old']}` -> `{fact['new']}` turns it red")
            ok = False
        if not ok:
            break
        level = 4 if label == "proof" else 5
    return level, problems, runs


# ---------------- the gate ----------------------------------------------------
def draft_answer(listing, verdicts, fact, level, verdict, runs, app):
    lines = ["# Blast radius", "", f"Verdict: {verdict}"]
    if level >= 4:
        r = runs["app" if level == 5 else "proof"]
        cmd = app if level == 5 else fact["proof"]
        lines.append(f"Level: {level} ({LEVELS[level]}: `{cmd}` failed with the break (exit {r['broken'][0]}) "
                     "and passed on the change)")
    else:
        lines.append(f"Level: {level} (unproven): {LEVELS[level]}; nothing was run that fails when the fact is false")
    lines.append("Change: [[fill: what the diff changes, in one sentence]]")
    if fact.get("fact"):
        lines.append(f"Fact: {fact['fact']}" + ("" if level >= 4 else " (not shown failing)"))
    if level >= 4:
        lines.append(f"Break: {fact['break']} `{fact['old']}` -> `{fact['new']}`")
    cons = listing["consumers"]
    lines += ["", f"Consumers outside the diff ({len(cons)}), base {listing['base']}:"]
    for cls in CLASSES:
        group = [(who, why) for who, (c, why) in verdicts.items() if c == cls]
        if group:
            lines.append(f"- {cls} ({len(group)}):")
            lines += [f"  - {who}: {why}" for who, why in sorted(group)]
    return "\n".join(lines) + "\n"


def gate(repo, app=None, timeout=300):
    ledger = read_json(repo, LEDGER, {})
    app = app or ledger.get("app")
    listing = read_json(repo, CONSUMERS)
    verdicts, unfilled = read_verdicts(repo)
    problems = {1: [], 2: [], 3: []}
    print('B = python "' + os.path.abspath(__file__) + '" ' + repo)
    now = shas(repo)

    # stage 1: a consumer list current with the code
    if listing is None:
        problems[1].append("no consumer list. Run B --base <ref>, the commit the change starts from")
    else:
        moved = sorted(f for f in set(now) | set(listing["shas"]) if now.get(f) != listing["shas"].get(f))
        if moved:
            problems[1].append(f"the code changed since the list ({', '.join(moved[:4])}"
                               f"{' ...' if len(moved) > 4 else ''}). Run B --base {listing['base']} again")

    # stage 2: every consumer has a verdict, and breaks/cleared cite what they rest on
    sites = [c["site"] for c in (listing or {}).get("consumers", [])]
    missing = [c for c in (listing or {}).get("consumers", []) if c["site"] not in verdicts]
    for who, (cls, why) in sorted(verdicts.items()):
        if who in sites or who.startswith("outside "):
            bad = verdict_problem(repo, cls, why)
            if bad:
                problems[2].append(f"{who}: {bad}")
    if missing:
        if not problems[1]:
            lines = read_text(repo, VERDICTS).splitlines() or VERDICTS_HEAD.rstrip("\n").splitlines() + [""]
            new = [f"- {c['site']}: [[fill: {' | '.join(CLASSES)}]]: [[fill: why, with the file:line; it uses "
                   f"{', '.join(c['what'])}: {c['text'].replace(']]', '] ]')}]]"
                   for c in missing if c["site"] not in unfilled]
            if new:
                write_file(repo, VERDICTS, "\n".join(lines + new) + "\n")
        problems[2].append(f"{len(missing)} consumer(s) have no verdict; their slots are in {VERDICTS}: "
                           + ", ".join(c["site"] for c in missing[:8]) + (" ..." if len(missing) > 8 else ""))
    breaks = sorted(w for w, (c, _) in verdicts.items() if c == "breaks" and (w in sites or w.startswith("outside ")))

    # stage 3: the one fact the change is safe because of, run red with it broken, green on the change
    fact = read_fact(repo)
    level, fact_problems, runs = fact_level(repo, fact, app, timeout)
    if not breaks:
        problems[3] = fact_problems if level < 4 else [p for p in fact_problems if "`app`" in p or "the app " in p]
    verdict = "breaks" if breaks else "safe" if level >= 4 else "unproven"
    write_json(repo, LEDGER, {"app": app, "breaks": breaks, "level": level, "shas": now, "verdict": verdict,
                              "runs": {k: {s: list(v) for s, v in r.items()} for k, r in runs.items()}})

    names = {1: "list: current with the code", 2: "account: every consumer has a verdict",
             3: f"fact: seen failing with the fact broken (level {level}: {LEVELS[level]})"}
    for g in (1, 2, 3):
        if g == 3 and breaks:
            print(f"STAGE 3 fact: not needed, {len(breaks)} consumer(s) break, so the answer is `breaks`")
            continue
        print(f"STAGE {g} {names[g]}: " + ("holds" if not problems[g] else f"open, {len(problems[g])} to fix"))
        for line in problems[g]:
            print(f"  - {line}")
    if not problems[1] and not problems[2]:
        text = draft_answer(listing, verdicts, fact, level, verdict, runs, app)
        write_file(repo, ANSWER, text)
        print(f"\nANSWER (drafted in {ANSWER}; fill its slots, then B --answer-check {ANSWER}):\n")
        print(text)
    open_stages = [g for g in (1, 2, 3) if problems[g]]
    if open_stages:
        print(f"BLAST-GATE: open({', '.join(map(str, open_stages))}): fix the lines above, then B --gate")
        return 1
    print(f"BLAST-GATE: done({len(sites)} consumers, verdict {verdict}, level {level})")
    return 0


def answer_check(repo, path):
    ledger = read_json(repo, LEDGER)
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        print(f"ANSWER-CHECK: cannot read {path}")
        return 2
    problems = []
    if ledger is None:
        print("ANSWER-CHECK: refused\n  - the helper has recorded nothing. Run B --gate first")
        return 1
    rel_answer = os.path.relpath(os.path.abspath(path), repo).replace(os.sep, "/")
    now = {f: s for f, s in shas(repo).items() if f != rel_answer}
    then = {f: s for f, s in ledger["shas"].items() if f != rel_answer}
    moved = sorted(f for f in set(now) | set(then) if now.get(f) != then.get(f))
    if moved:
        problems.append(f"the code changed since the last gate ({', '.join(moved[:4])}). Run B --gate again")
    level, verdict = ledger["level"], ledger["verdict"]
    if FILL in text:
        problems.append("unfilled [[fill: ...]] slot(s): write what each asks")
    m = re.search(r"(?im)^\s*Level:\s*(\d)", text)
    if not m:
        problems.append(f"no `Level: N` line. Copy it from {ANSWER}: the helper recorded {level}")
    elif int(m.group(1)) > level:
        problems.append(f"states level {m.group(1)}, but the helper recorded {level}. Use the level line from {ANSWER}")
    v = re.search(r"(?im)^\s*Verdict:\s*(\w+)", text)
    if v and v.group(1).lower() != verdict:
        problems.append(f"states verdict {v.group(1)}, but the helper recorded {verdict}")
    says_safe = bool(re.search(r"(?i)(?<!not )\bsafe\b", text))
    if says_safe and level < 4:
        problems.append(f"says safe at level {level}: `safe` needs a proof seen failing with the fact broken "
                        "(level 4). Say `unproven`, or finish stage 3 and run B --gate")
    if says_safe and ledger.get("breaks"):
        problems.append(f"says safe, but {len(ledger['breaks'])} consumer(s) break: {', '.join(ledger['breaks'][:4])}")
    if level < 4 and not re.search(r"(?i)\bunproven\b", text):
        problems.append(f"below level 4 the answer must say `unproven` (the helper recorded {level})")
    if problems:
        print("ANSWER-CHECK: refused")
        print("".join(f"  - {p}\n" for p in problems), end="")
        return 1
    print(f"ANSWER OK (verdict {verdict}, level {level})")
    return 0


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description="List what a change breaks outside its diff, and prove why not.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--base", help="the commit the change starts from: list every consumer outside the diff")
    ap.add_argument("--gate", action="store_true", help="check the stages and draft the answer")
    ap.add_argument("--app", help="a command that shows the fact in the running app (level 5)")
    ap.add_argument("--answer-check", metavar="FILE", help="refuse an answer the helper's record does not back")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per command")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo)
    if a.answer_check:
        return answer_check(repo, a.answer_check)
    if a.base:
        code = list_consumers(repo, a.base)
        if code or not (a.gate or a.app):
            return code
        print()
    if a.gate or a.app:
        return gate(repo, a.app, a.timeout)
    print("B --base <ref> lists every consumer of what the diff changed; B --gate checks the stages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
