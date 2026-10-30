#!/usr/bin/env python3
"""formal.py - the mechanical side of the formal-check skill.

A formal check (a model checker, a prover, a code-level verifier, an exhaustive enumerator) covers
every case in its scope, but only of what it describes. This holds a check to what can be run and
compared: it passes on the code, it fails with the guarded code broken, its model points at lines
that exist, its property never weakens silently, and it goes stale the moment the code it covers
changes:

  F --scan                candidate targets (concurrency, retries, state, parsers, unsafe code),
                          with file:line; .formal/candidates.md
  F --gate [NAME]         check the stages of every check in .formal/<name>.md (or one), print
                          every problem with its fix, draft .formal/answer.md:
    1 record  every field is there; the target and model files exist
    2 map     each `map: <model element> -> <file:line>` names an element in the model and a line
              that exists in a covered file; every covered file has a map line
    3 run     the command passes on a copy of the working tree within the budget, or fails and is
              told as `step:` lines (a bug); in CI when the repo has CI
    4 break   one edit to a covered file (never the model) makes the command fail
    5 sync    the property, bounds and assumptions match the lock unless a `changed:` line with
              evidence says otherwise; every commit to covered code since the sync commit is
              classified in .formal/<name>.drift.md
  F --drift [NAME]        the commits since each sync commit that touched covered code, renames
                          followed; drafts .formal/<name>.drift.md
  F --answer-check FILE   refuse a reply that claims more than the gate recorded

Outcomes: in-sync, updated, bug, blocked, stale, open. Only the gate writes the sync commit.
The product tree is never written: commands run in throwaway copies, and only .formal/ changes.
`F` is `python formal.py <repo>`. Stdlib only.
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _encoding import utf8_streams  # noqa: E402

STATE = ".formal"
ANSWER = f"{STATE}/answer.md"
CANDIDATES = f"{STATE}/candidates.md"
LEDGER = f"{STATE}/state.json"
FILL = "[[fill"
# Folders that hold tools' state or caches, never the product: not scanned, copied or compared.
NOT_PRODUCT = {".git", "__pycache__", "node_modules", ".venv", "venv", STATE, ".verify-state",
               ".verify-state-cache", ".wire", ".features", ".release", ".evolve", ".perf", ".latent",
               ".debug", ".structure", ".threat", ".blast", ".mistakes", ".pytest_cache", ".mypy_cache",
               ".ruff_cache"}
NOT_PRODUCT_FILES = {".verify-state.json"}
CI_FILES = re.compile(r"^(\.github/workflows/[^/]+\.ya?ml|\.gitlab-ci\.yml|\.circleci/config\.yml|"
                      r"azure-pipelines\.yml|Jenkinsfile|\.buildkite/.+|bitbucket-pipelines\.yml)$")
REQUIRED = ("property", "harm", "target", "tool", "cmd", "model", "covers", "bounds", "assumes")
LISTS = {"model", "map", "covers", "step", "changed"}
LOCKED = ("property", "bounds", "assumes")
KINDS = ("no-effect", "reshaped", "promise-changed", "suspect")
FILE_LINE = re.compile(r"([\w./\\-]+):(\d+)$")
NOT_FOUND = (127, 9009)
BASH = shutil.which("bash")
SCAN = [("concurrency", re.compile(r"\b(lock|mutex|semaphore|atomic|thread|threading|asyncio|await|async\s+def|"
                                   r"goroutine|chan\b|synchronized|volatile|race|concurrent)", re.I)),
        ("retry", re.compile(r"\b(retry|retries|backoff|attempts?|idempoten)", re.I)),
        ("state", re.compile(r"\b(state\s*(==|=|\bin\b)|transition|status\s*==|fsm|state_machine)", re.I)),
        ("parser", re.compile(r"\b(parse|tokeni[sz]e|lexer|decode|deserializ)", re.I)),
        ("unsafe", re.compile(r"\b(unsafe|ctypes|memcpy|malloc|free\(|ptr::|transmute)", re.I))]
CODE_EXT = (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".c", ".h", ".cc", ".cpp", ".hpp", ".java",
            ".kt", ".swift", ".rb", ".cs", ".scala", ".ex", ".exs", ".erl", ".zig")
CHECK_HEAD = """# One check per file: .formal/<name>.md, one-line fields:
#   - property: <the promise, one plain sentence>      - harm: <who is hurt when it breaks>
#   - target: <file:line of the promise in the code>   - tool: <name> <version>
#   - cmd: `<command, exit 0 when the property holds>` - model: <model or harness path> (one or more)
#   - map: <model element> -> <file:line>  (one or more)  - covers: <code path> (one or more)
#   - bounds: <what the run is limited to>             - assumes: <what it takes for granted>
#   - break: <covered file>  - old: `<text>`  - new: `<text>`   (makes the property false)
#   - step: <what happens> <file:line>   (two or more, only when the command fails on the code)
#   - changed: <old> -> <new> evidence: <sha|file:line>   (when the property, bounds or assumes move)
"""


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
        with open(os.path.join(repo, *rel_path.split("/")), "rb") as fh:
            return fh.read()
    except OSError:
        return None


def read_text(repo, rel_path):
    data = read_bytes(repo, rel_path)
    return None if data is None else data.decode("utf-8", errors="replace")


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


def commit_of(repo, ref):
    code, out, _ = git(repo, "rev-parse", "--verify", "-q", ref + "^{commit}")
    return out.strip() if code == 0 and out.strip() else None


def line_problem(repo, cite):
    """None when CITE (file:line) names a line that exists, else why not."""
    m = FILE_LINE.match(cite.strip())
    if not m:
        return f"{cite} is not file:line"
    f, n = m.group(1).replace("\\", "/"), int(m.group(2))
    text = read_text(repo, f)
    if text is None:
        return f"{f} does not exist"
    if n < 1 or n > len(text.splitlines()):
        return f"{f}:{n} is past the end of the file"
    return None


def evidence_ok(repo, item):
    return bool(commit_of(repo, item)) if re.match(r"^[0-9a-f]{4,40}$", item) else line_problem(repo, item) is None


# ---------------- the checks --------------------------------------------------
def unquote(v):
    v = v.strip()
    return v[1:-1] if len(v) > 1 and v[0] == "`" and v[-1] == "`" else v


def read_checks(repo, only=None):
    """{name: {field: value or [values]}} from .formal/<name>.md."""
    d = os.path.join(repo, STATE)
    out = {}
    for n in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not n.endswith(".md") or n.endswith(".drift.md") or n in ("answer.md", "candidates.md"):
            continue
        name = n[:-3]
        if only and name != only:
            continue
        c = {k: [] for k in LISTS}
        for line in read_text(repo, f"{STATE}/{n}").splitlines():
            m = re.match(r"^\s*-\s*([a-z-]+):\s*(.*?)\s*$", line)
            if not m:
                continue
            k, v = m.group(1), m.group(2)
            if k in LISTS:
                c[k].append(unquote(v).replace("\\", "/") if k in ("model", "covers") else v)
            else:
                c[k] = unquote(v) if k in ("cmd", "old", "new") else v.replace("\\", "/") if k == "break" else v
        out[name] = c
    return out


def covered(path, covers):
    return any(path == c or path.startswith(c.rstrip("/") + "/") for c in covers)


def copy_tree(repo, dest):
    def ignore(d, names):
        return [n for n in names if n in NOT_PRODUCT or n in NOT_PRODUCT_FILES or n.endswith(".pyc")]
    shutil.copytree(repo, dest, ignore=ignore)


def run_cmd(cmd, cwd, budget):
    """(exit or 'timeout', last output line, seconds)."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    # The agent writes commands in the shell it uses (`VAR=x cmd`, `&&`), so prefer bash.
    argv = [BASH, "-c", cmd] if BASH else cmd
    start = time.monotonic()
    try:
        r = subprocess.run(argv, cwd=cwd, shell=not BASH, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=budget, env=env)
    except subprocess.TimeoutExpired:
        return "timeout", "timed out", time.monotonic() - start
    text = ((r.stdout or "") + (r.stderr or "")).replace(cwd, "<repo>")
    tail = [ln for ln in text.splitlines() if ln.strip()]
    code = r.returncode
    if code != 0 and re.search(r"command not found|is not recognized as an internal or external", text):
        code = 127
    return code, tail[-1][:160] if tail else "", time.monotonic() - start


def run_copy(repo, cmd, budget, edit=None):
    """Run CMD in a throwaway copy of the working tree, with EDIT (file, old, new) applied first."""
    tmp = tempfile.mkdtemp(prefix="formal-")
    try:
        root = os.path.join(tmp, "repo")
        copy_tree(repo, root)
        if edit:
            f, old, new = edit
            p = os.path.join(root, *f.split("/"))
            with open(p, encoding="utf-8", errors="replace", newline="") as fh:
                text = fh.read()
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(text.replace(old, new, 1))
        return run_cmd(cmd, root, budget)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------- drift -------------------------------------------------------
def drift_commits(repo, sync, covers):
    """[(sha, subject, [touched paths], [(old, new) renames])] since SYNC, oldest first, renames followed."""
    if not commit_of(repo, sync):
        return []
    code, out, _ = git(repo, "log", "--reverse", "-M", "--name-status", "--format=%x00%H%x09%s", f"{sync}..HEAD")
    if code != 0:
        return []
    names, found = list(covers), []
    for chunk in out.split("\0")[1:]:
        head, _, body = chunk.partition("\n")
        sha, _, subject = head.partition("\t")
        touched, renames = [], []
        for line in body.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            if parts[0].startswith("R") and len(parts) == 3:
                old, new = parts[1], parts[2]
                if covered(old, names):
                    touched.append(old)
                    renames.append((old, new))
                    names.append(new)
            elif covered(parts[1], names):
                touched.append(parts[1])
        if touched:
            found.append((sha, subject, touched, renames))
    return found


def read_drift(repo, name):
    """{sha prefix: (kind, why)} from .formal/<name>.drift.md, filled lines only."""
    out = {}
    for line in (read_text(repo, f"{STATE}/{name}.drift.md") or "").splitlines():
        m = re.match(r"^\s*-\s*([0-9a-f]{7,40}):\s*(" + "|".join(KINDS) + r"):\s*(.+?)\s*$", line)
        if m and FILL not in line:
            out[m.group(1)] = (m.group(2), m.group(3))
    return out


def drift(repo, only=None):
    checks = read_checks(repo, only)
    if not checks:
        print(f"DRIFT: no checks in {STATE}/. Write .formal/<name>.md first.")
        return 1
    for name, c in checks.items():
        lock = read_json(repo, f"{STATE}/{name}.lock")
        if not lock or not lock.get("sync"):
            print(f"{name}: no sync commit yet. Run F --gate until it passes once.")
            continue
        commits = drift_commits(repo, lock["sync"], c["covers"])
        if not commits:
            print(f"{name}: in-sync: no commit since {lock['sync'][:10]} touched {', '.join(c['covers'])}")
            continue
        print(f"{name}: {len(commits)} commit(s) since {lock['sync'][:10]} touched covered code:")
        have = read_drift(repo, name)
        lines = [ln for ln in (read_text(repo, f"{STATE}/{name}.drift.md") or "").splitlines()
                 if ln.strip() and FILL not in ln]
        for sha, subject, touched, renames in commits:
            print(f"  - {sha[:10]} {subject} ({', '.join(touched)})")
            for old, new in renames:
                print(f"      renamed: {old} -> {new}; update covers and every map line")
            if not any(sha.startswith(k) for k in have):
                lines.append(f"- {sha[:10]}: [[fill: no-effect|reshaped|promise-changed|suspect]]: "
                             "[[fill: why, from the diff; promise-changed cites evidence: <sha|file:line>]]")
        write_file(repo, f"{STATE}/{name}.drift.md", "\n".join(lines) + "\n")
        print(f"  classify each in {STATE}/{name}.drift.md, update the model from the code, then F --gate")
    return 0


# ---------------- scan --------------------------------------------------------
def scan(repo):
    hits = {}
    for f in product_files(repo):
        if not f.endswith(CODE_EXT):
            continue
        for i, line in enumerate(read_text(repo, f).splitlines(), 1):
            kinds = [k for k, rx in SCAN if rx.search(line)]
            if kinds:
                hits.setdefault(f, []).append((i, kinds, line.strip()[:100]))
    if not hits:
        print("SCAN: no candidates found. Name the promise yourself: where does a break harm users "
              "while the tests rarely reach the case that breaks it?")
        write_file(repo, CANDIDATES, "# Candidates\n\nnone found\n")
        return 0
    lines = ["# Candidates", "", "Ranked by hits. Choose the promise whose break costs the most and that the "
             "tests reach the least, not the easiest one to verify.", ""]
    for f in sorted(hits, key=lambda f: -len(hits[f])):
        lines.append(f"## {f} ({len(hits[f])})")
        lines += [f"- {f}:{i} [{', '.join(k)}] {t}" for i, k, t in hits[f]]
        lines.append("")
    write_file(repo, CANDIDATES, "\n".join(lines))
    print("\n".join(lines))
    print(f"SCAN: {sum(map(len, hits.values()))} line(s) in {len(hits)} file(s); kept in {CANDIDATES}")
    return 0


# ---------------- the gate ----------------------------------------------------
def lock_hash(c):
    return hashlib.sha256("\n".join(c.get(k, "") for k in LOCKED).encode()).hexdigest()[:16]


def gate(repo, only=None, budget=600):
    print('F = python "' + os.path.abspath(__file__) + '" ' + repo)
    checks = read_checks(repo, only)
    files = product_files(repo)
    ci = [f for f in files if CI_FILES.match(f)]
    ci_text = "\n".join(read_text(repo, f) for f in ci)
    problems = {g: [] for g in (1, 2, 3, 4, 5)}
    if not checks:
        problems[1].append(f"no check in {STATE}/{only or '<name>'}.md. Run F --scan, choose a target, and "
                           "write one:\n" + CHECK_HEAD)
    head = commit_of(repo, "HEAD")
    record = {}
    for name, c in checks.items():
        before = sum(map(len, problems.values()))

        def flag(stage, text):
            problems[stage].append(f"{name}: {text}")

        rec = record[name] = {"outcome": "open", "notes": []}
        # stage 1: the record
        for k in REQUIRED:
            if not c.get(k):
                flag(1, f"missing `- {k}:`")
        if c.get("target"):
            why = line_problem(repo, c["target"])
            if why:
                flag(1, f"target {why}")
        for m in c["model"]:
            if read_text(repo, m) is None:
                flag(1, f"model {m} does not exist")
        model_text = "\n".join(read_text(repo, m) or "" for m in c["model"])

        # stage 2: the map
        mapped = set()
        for item in c["map"]:
            elem, arrow, cite = item.partition("->")
            elem, cite = elem.strip().strip("`"), cite.strip()
            if not arrow or not elem or not cite:
                flag(2, f"map `{item}` is not `<model element> -> <file:line>`")
                continue
            why = line_problem(repo, cite)
            if why:
                flag(2, f"map {why}")
            if c["model"] and elem not in model_text:
                flag(2, f"map element `{elem}` is not in {', '.join(c['model'])}")
            f = FILE_LINE.match(cite)
            f = f.group(1).replace("\\", "/") if f else cite
            if not covered(f, c["covers"]):
                flag(2, f"map {cite} points outside covers ({', '.join(c['covers']) or 'none'})")
            mapped.add(f)
        for cov in c["covers"]:
            if not any(covered(f, [cov]) for f in mapped):
                flag(2, f"covers {cov} has no map line: point a model element at the code it stands for")

        # stage 3: the run on the code
        cmd, clean = c.get("cmd"), None
        if cmd:
            clean = run_copy(repo, cmd, budget)
            rec["run"] = list(clean)
            code, last, secs = clean
            if code == "timeout":
                flag(3, f"`{cmd}` took more than {budget} s: too slow to rerun on every change. Shrink the bound "
                        "and say so in `- bounds:`, or raise --budget")
            elif code in NOT_FOUND:
                rec["outcome"] = "blocked"
                flag(3, f"blocked: `{cmd}` exit {code}: {last}. Install the tool, or say why it cannot run here")
            elif code == 0:
                print(f"{name}: `{cmd}` passed in {secs:.1f} s")
            else:
                steps = c["step"]
                bad = [s for s in steps if line_problem(repo, s.split()[-1] if s.split() else "")]
                for s in bad:
                    flag(3, "step " + line_problem(repo, s.split()[-1] if s.split() else ""))
                if len(steps) < 2:
                    flag(3, f"`{cmd}` fails on the code: a bug needs two or more `- step:` lines, each a "
                            f"thing the code does, ending in the file:line it happens at (exit {code}: {last}). "
                            "Never weaken the property or the model to make it pass")
                elif not bad:
                    rec["outcome"] = "bug"
                    rec["steps"] = steps
            if ci and cmd not in ci_text:
                flag(3, f"`{cmd}` is not in the CI config ({', '.join(ci)}). Run the same command there")

        # stage 4: the break makes it fail
        if clean and clean[0] == 0:
            b, old, new = c.get("break"), c.get("old"), c.get("new")
            if not (b and old is not None and new is not None):
                flag(4, "no break: `- break: <covered file>`, `- old: `<text>``, `- new: `<text>`` that make "
                        "the property false in the code")
            elif b in c["model"]:
                flag(4, f"the break edits {b}, a model file; break the code it covers")
            elif not covered(b, c["covers"]):
                flag(4, f"the break edits {b}, which covers does not list")
            else:
                text = read_text(repo, b)
                n = 0 if text is None else text.count(old)
                if n != 1:
                    flag(4, f"the break's old text is not in {b}" if n == 0 else
                            f"the break's old text occurs {n} times in {b}; make it unique")
                else:
                    broken = run_copy(repo, cmd, budget, (b, old, new))
                    rec["broken"] = list(broken)
                    if broken[0] == 0:
                        flag(4, f"`{cmd}` still passes with the break applied: it cannot fail. Make the model "
                                "describe the code it covers, or break what the property guards")
                    elif broken[0] == "timeout":
                        flag(4, f"`{cmd}` took more than {budget} s with the break applied: too slow to rerun")

        # stage 5: the lock and the drift
        lock = read_json(repo, f"{STATE}/{name}.lock")
        changes = []
        if lock:
            for k in LOCKED:
                if c.get(k, "") == lock.get(k, ""):
                    continue
                said = [ch for ch in c["changed"]
                        if (m := re.match(r"^(.*?)\s*->\s*(.*?)\s+evidence:\s*(\S+)\s*$", ch))
                        and m.group(1) == lock.get(k, "") and m.group(2) == c.get(k, "")]
                if not said:
                    flag(5, f"the {k} changed since it was locked; add `- changed: {lock.get(k, '')} -> "
                            f"{c.get(k, '')} evidence: <sha|file:line>` naming the change that made it so, or "
                            "put it back")
                    continue
                ev = re.search(r"evidence:\s*(\S+)\s*$", said[-1]).group(1)
                if not evidence_ok(repo, ev):
                    flag(5, f"evidence {ev} is not a commit or a line in this repo")
                else:
                    changes.append(f"{k} changed: {lock.get(k, '')} -> {c.get(k, '')} (evidence {ev})")
            commits = drift_commits(repo, lock.get("sync", ""), c["covers"])
            if commits:
                rec["stale"] = [s[:10] for s, *_ in commits]
                have = read_drift(repo, name)
                missing = []
                for sha, *_ in commits:
                    hit = [v for k, v in have.items() if sha.startswith(k)]
                    if not hit:
                        missing.append(sha)
                    elif hit[0][0] == "promise-changed":
                        ev = re.search(r"evidence:\s*(\S+)", hit[0][1])
                        if not ev:
                            flag(5, f"{sha[:10]} is promise-changed with no evidence: add `evidence: "
                                    "<sha|file:line>` (the doc, test or changelog that says so)")
                        elif not evidence_ok(repo, ev.group(1)):
                            flag(5, f"evidence {ev.group(1)} is not a commit or a line in this repo")
                if missing:
                    rec["outcome"] = "stale" if rec["outcome"] == "open" else rec["outcome"]
                    flag(5, f"stale: {len(missing)} commit(s) touched covered code since {lock['sync'][:10]}. "
                            "Run F --drift, classify each, update the model from the code")
                    for sha in missing:
                        flag(5, f"{sha[:10]} has no drift line in {STATE}/{name}.drift.md")
        rec["notes"] = changes
        for note in changes:
            print(f"{name}: {note}")
        if c["covers"] and head:
            dirty = git(repo, "status", "--porcelain", "--", *c["covers"])[1].strip()
            if dirty and clean and clean[0] == 0:
                flag(5, f"covered files have uncommitted changes ({dirty.splitlines()[0].strip()}); commit them "
                        "so the sync commit describes the code that passed")

        clear = sum(map(len, problems.values())) == before
        if clear and rec["outcome"] == "open":
            rec["outcome"] = "updated" if lock and rec.get("stale") else "in-sync"
            if head:
                write_file(repo, f"{STATE}/{name}.lock", json.dumps(
                    {**{k: c.get(k, "") for k in LOCKED}, "hash": lock_hash(c), "sync": head,
                     "cmd": cmd, "changes": (lock or {}).get("changes", []) + changes}, indent=1) + "\n")
        elif rec["outcome"] == "open" and lock and rec.get("stale"):
            rec["outcome"] = "stale"

    names = {1: "record: every field, the target and model exist", 2: "map: model elements point at covered code",
             3: "run: passes on the code, or a bug told as steps", 4: "break: one edit to the code makes it fail",
             5: "sync: the lock holds and every commit since is classified"}
    for g in (1, 2, 3, 4, 5):
        print(f"STAGE {g} {names[g]}: " + ("holds" if not problems[g] else f"open, {len(problems[g])} to fix"))
        for line in problems[g]:
            print(f"  - {line}")
    print("\nCHECKS:")
    for name, rec in record.items():
        print(f"  {name}: {rec['outcome']}")
    ledger = read_json(repo, LEDGER, {}) or {}
    ledger.setdefault("checks", {}).update(record)
    if not only:
        ledger["checks"] = record
    ledger.update(shas=shas(repo), ci=ci)
    write_file(repo, LEDGER, json.dumps(ledger, indent=1, sort_keys=True) + "\n")
    if record:
        text = draft_answer(checks, record, ci)
        write_file(repo, ANSWER, text)
        print(f"\nANSWER (drafted in {ANSWER}; fill its slots, then F --answer-check {ANSWER}):\n")
        print(text)
    open_stages = [g for g in (1, 2, 3, 4, 5) if problems[g]]
    if open_stages:
        print(f"FORMAL-GATE: open({', '.join(map(str, open_stages))}): fix the lines above, then F --gate")
        return 1
    counts = {o: sum(r["outcome"] == o for r in record.values()) for o in ("in-sync", "updated", "bug")}
    print(f"FORMAL-GATE: done({len(record)} checks: {counts['in-sync']} in-sync, {counts['updated']} updated, "
          f"{counts['bug']} bug)")
    return 0


def draft_answer(checks, record, ci):
    lines = ["# Formal check", "",
             "CI: " + (", ".join(ci) if ci else "no CI config found; the checks run locally only")]
    for name, rec in record.items():
        c = checks[name]
        lines += ["", f"## {name}", f"Outcome: {rec['outcome']}",
                  f"Property: {c.get('property', '')}", f"Harm: {c.get('harm', '')}",
                  f"Tool: {c.get('tool', '')}, run with `{c.get('cmd', '')}`",
                  f"Bounds: {c.get('bounds', '')}", f"Assumes: {c.get('assumes', '')}"]
        if rec.get("run"):
            lines.append(f"Run on the code: exit {rec['run'][0]} in {rec['run'][2]:.1f} s")
        if rec.get("broken"):
            lines.append(f"Run with `{c.get('old')}` -> `{c.get('new')}` in {c.get('break')}: exit "
                         f"{rec['broken'][0]} ({rec['broken'][1]})")
        if rec.get("steps"):
            lines.append("Counterexample, in the code's words:")
            lines += [f"{i}. {s}" for i, s in enumerate(rec["steps"], 1)]
        if rec.get("stale"):
            lines.append("Commits since the sync: " + ", ".join(rec["stale"]))
        lines += rec.get("notes", [])
        lines.append("Not covered: [[fill: what this pass does not cover beyond its bounds and assumptions]]")
    return "\n".join(lines) + "\n"


def answer_check(repo, path):
    ledger = read_json(repo, LEDGER)
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        print(f"ANSWER-CHECK: cannot read {path}")
        return 2
    if ledger is None:
        print("ANSWER-CHECK: refused\n  - the gate has recorded nothing. Run F --gate first")
        return 1
    problems = []
    now, then = shas(repo), ledger.get("shas", {})
    moved = sorted(f for f in set(now) | set(then) if now.get(f) != then.get(f))
    if moved:
        problems.append(f"the code changed since the last gate ({', '.join(moved[:4])}). Run F --gate again")
    if FILL in text:
        problems.append("unfilled [[fill: ...]] slot(s): write what each asks")
    recorded = ledger.get("checks", {})
    seen = set()
    for m in re.finditer(r"(?m)^##\s+(\S+)\s*\n((?:(?!##\s).*\n?)*)", text):
        name, body = m.group(1), m.group(2)
        seen.add(name)
        rec = recorded.get(name)
        if rec is None:
            problems.append(f"names {name}, a check the gate did not record")
            continue
        s = re.search(r"(?im)^\s*Outcome:\s*([\w-]+)", body)
        if s and s.group(1).lower() != rec["outcome"]:
            problems.append(f"calls {name} {s.group(1).lower()}, but the gate recorded it {rec['outcome']}")
        elif not s:
            problems.append(f"{name} has no `Outcome:` line; copy it from {ANSWER}")
    for name in recorded:
        if name not in seen:
            problems.append(f"leaves out {name}; copy its section from {ANSWER}")
    if problems:
        print("ANSWER-CHECK: refused")
        print("".join(f"  - {p}\n" for p in problems), end="")
        return 1
    print(f"ANSWER OK ({len(recorded)} checks: "
          + ", ".join(f"{n} {r['outcome']}" for n, r in recorded.items()) + ")")
    return 0


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description="Hold a formal check to the code it describes.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--scan", action="store_true", help="list candidate targets")
    ap.add_argument("--gate", nargs="?", const="", metavar="NAME", help="check the stages and draft the reply")
    ap.add_argument("--drift", nargs="?", const="", metavar="NAME", help="commits to covered code since the sync")
    ap.add_argument("--answer-check", metavar="FILE", help="refuse a reply the gate's record does not back")
    ap.add_argument("--budget", type=int, default=600, help="seconds a check run may take")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo)
    if a.answer_check:
        return answer_check(repo, a.answer_check)
    if a.scan:
        return scan(repo)
    if a.drift is not None:
        return drift(repo, a.drift or None)
    if a.gate is not None:
        return gate(repo, a.gate or None, a.budget)
    print("F --scan lists candidates; F --gate checks the stages; F --drift lists commits since the sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
