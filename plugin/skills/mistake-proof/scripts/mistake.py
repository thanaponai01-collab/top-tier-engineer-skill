#!/usr/bin/env python3
"""mistake.py - the mechanical side of the mistake-proof skill.

Agents keep making the same mistakes, and a new line in CLAUDE.md does not stop the next one:
nothing fails when it is skipped. This groups past mistakes into classes, asks for the strongest
fix that works, and will not accept a check until it ran red where the mistake happened and green
on the fix:

  M --mine [--since REF]  candidates from history (reverts, commits that bring a reverted change
                          back, fixes naming an earlier commit, workaround comments);
                          .mistakes/candidates.md, and a classes.md to fill
  M --add "TEXT"          record a correction the operator gave, dated; evidence `added:N`
  M --gate                check the stages, print every problem with its fix, draft the reply:
    1 classes  each class has 2 pieces of evidence that exist
    2 level    a level 1-5, and `why not K` for every stronger level K
    3 proof    levels 1-4: the check fails on the mistake commit and passes on the working tree,
               and runs in CI when the repo has CI
    4 rules    the agent file's rule table has a row per class whose enforcer exists; a level-5
               rule that recurred after it was added is a repeat; every `mistake-ok:` exception
               has a reason, a date still to come and a human's approval
  M --answer-check FILE   refuse a reply that claims more than the gate recorded

Levels: 1 architecture, 2 types, 3 a lint or CI check, 4 a test, 5 docs only (unenforced).
The product tree is never written: checks run in throwaway copies, and only .mistakes/ changes.
`M` is `python mistake.py <repo>`. Stdlib only.
"""
import argparse, datetime, hashlib, io, json, os, re, shutil, subprocess, sys, tarfile, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _encoding import utf8_streams  # noqa: E402

STATE = ".mistakes"
CLASSES = f"{STATE}/classes.md"
CANDIDATES = f"{STATE}/candidates.md"
ADDED = f"{STATE}/added.md"
RULES_DRAFT = f"{STATE}/rules.md"
LEDGER = f"{STATE}/state.json"
ANSWER = f"{STATE}/answer.md"
FILL = "[[fill"
# Folders that hold tools' state or caches, never the product: not scanned, copied or compared.
NOT_PRODUCT = {".git", "__pycache__", "node_modules", ".venv", "venv", STATE, ".verify-state",
               ".verify-state-cache", ".wire", ".features", ".release", ".evolve", ".perf", ".latent",
               ".debug", ".structure", ".threat", ".blast", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
NOT_PRODUCT_FILES = {".verify-state.json"}
LEVELS = {1: "architecture", 2: "types", 3: "a lint or CI check", 4: "a test",
          5: "docs only: nothing fails when an agent skips it"}
AGENT_FILES = ("CLAUDE.md", "AGENTS.md")
CI_FILES = re.compile(r"^(\.github/workflows/[^/]+\.ya?ml|\.gitlab-ci\.yml|\.circleci/config\.yml|"
                      r"azure-pipelines\.yml|Jenkinsfile|\.buildkite/.+|bitbucket-pipelines\.yml)$")
OPEN_MARK, CLOSE_MARK = "<!-- mistake-rules -->", "<!-- /mistake-rules -->"
WORKAROUND = re.compile(r"(#|//|/\*|--)\s*(don'?t|do not|never|must|NOTE:|HACK|XXX|workaround)\b", re.I)
SHA = re.compile(r"^[0-9a-f]{4,40}$")
FILE_LINE = re.compile(r"^([\w./\\-]+):(\d+)$")
BASH = shutil.which("bash")
CLASSES_HEAD = """# Mistake classes

One section per class of mistake that happened at least twice. Fill from candidates.md:

    ## <class-name>
    - evidence: <commit sha> | <file:line> | added:<N from M --add>   (two or more lines)
    - level: 1 architecture | 2 types | 3 lint or CI check | 4 test | 5 docs only
    - why not 1: <why architecture did not work>   (one line per level stronger than yours)
    - check: `<command that exits non-zero on the mistake>`            (levels 1-4)
    - mistake: <the commit where the mistake is present>               (levels 1-4)
    - check-files: <files the check needs, copied onto that commit>    (optional)

"""


# ---------------- the repo ----------------------------------------------------
def git(repo, *args, binary=False):
    p = subprocess.run(["git", "--no-optional-locks", "-c", "core.quotePath=false", "-C", repo, *args],
                       capture_output=True, **({} if binary else
                                               {"text": True, "encoding": "utf-8", "errors": "replace"}))
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


def commit_of(repo, ref):
    code, out, _ = git(repo, "rev-parse", "--verify", "-q", ref + "^{commit}")
    return out.strip() if code == 0 and out.strip() else None


def commit_date(repo, sha):
    return git(repo, "show", "-s", "--format=%cs", sha)[1].strip()


def today():
    return datetime.date.today().isoformat()


# ---------------- mining ------------------------------------------------------
def added_lines(repo, sha):
    _, out, _ = git(repo, "show", "--format=", "-U0", sha)
    return {ln[1:].strip() for ln in out.splitlines()
            if ln.startswith("+") and not ln.startswith("+++") and len(ln[1:].strip()) > 3}


def mine(repo, since=None):
    rng = [f"{since}..HEAD"] if since else ["HEAD"]
    code, out, err = git(repo, "log", "--format=%H%x1f%cs%x1f%s%x1f%b%x1e", *rng)
    if code:
        print(f"M --mine: git log failed: {err.strip()}")
        return 2
    log = []   # newest first
    for rec in out.split("\x1e"):
        parts = rec.strip("\n").split("\x1f")
        if len(parts) == 4:
            log.append(dict(zip(("sha", "date", "subject", "body"), parts)))
    order = {c["sha"]: i for i, c in enumerate(log)}
    reverts, redos, fixes = [], [], []
    for c in log:
        if c["subject"].startswith('Revert "'):
            m = re.search(r"reverts commit ([0-9a-f]{7,40})", c["body"])
            target = commit_of(repo, m.group(1)) if m else None
            if not target:
                continue
            reverts.append(f"- revert: {c['sha'][:10]} ({c['date']}) reverts {target[:10]}: {c['subject']}")
            undone = added_lines(repo, target)
            for later in log[:order[c["sha"]]]:
                back = undone & added_lines(repo, later["sha"])
                if back:
                    redos.append(f"- redo: {later['sha'][:10]} ({later['date']}) brings back what "
                                 f"{c['sha'][:10]} reverted from {target[:10]}: `{sorted(back)[0][:80]}`")
        elif re.search(r"(?i)\bfix", c["subject"] + " " + c["body"]):
            for tok in re.findall(r"\b[0-9a-f]{7,40}\b", c["subject"] + " " + c["body"]):
                earlier = commit_of(repo, tok)
                if earlier and earlier != c["sha"]:
                    fixes.append(f"- fix: {c['sha'][:10]} ({c['date']}) fixes {earlier[:10]}: {c['subject']}")
    comments = []
    for f in product_files(repo):
        for i, ln in enumerate(read_text(repo, f).splitlines(), 1):
            if WORKAROUND.search(ln) and "mistake-ok:" not in ln:
                comments.append(f"- comment: {f}:{i}: `{ln.strip()[:100]}`")
    lines = ["# Mistake candidates", "", f"Mined {len(log)} commit(s){' since ' + since if since else ''}. "
             "A class counts once it has happened twice; group these in classes.md.", ""]
    for title, group in (("Reverts", reverts), ("Brought back after a revert", redos),
                         ("Fixes that name an earlier commit", fixes), ("Workaround comments", comments[:50])):
        lines += [f"## {title} ({len(group)})", *group, ""]
    added = read_text(repo, ADDED).strip()
    if added:
        lines += ["## Corrections recorded with M --add", *added.splitlines()[1:], ""]
    write_file(repo, CANDIDATES, "\n".join(lines))
    if not read_text(repo, CLASSES):
        write_file(repo, CLASSES, CLASSES_HEAD)
    print("\n".join(lines))
    print(f"Written to {CANDIDATES}. Group the repeats into {CLASSES}, then M --gate.")
    return 0


def add(repo, text):
    entries = read_added(repo)
    n = max(entries, default=0) + 1
    body = read_text(repo, ADDED) or "# Corrections the operator gave (M --add)\n"
    write_file(repo, ADDED, body.rstrip("\n") + f"\n- {n} {today()}: {' '.join(text.split())}\n")
    print(f"recorded as added:{n} ({today()}). Use `- evidence: added:{n}` in {CLASSES}.")
    return 0


def read_added(repo):
    out = {}
    for ln in read_text(repo, ADDED).splitlines():
        m = re.match(r"^- (\d+) (\d{4}-\d\d-\d\d): (.*)$", ln)
        if m:
            out[int(m.group(1))] = (m.group(2), m.group(3))
    return out


# ---------------- classes -----------------------------------------------------
def read_classes(repo):
    """{name: {"evidence": [...], key: value}} from classes.md, in file order."""
    out, cur = {}, None
    for ln in read_text(repo, CLASSES).splitlines():
        if ln.startswith("    "):
            continue   # the indented example in the header
        m = re.match(r"^##\s+(\S+)\s*$", ln)
        if m:
            cur = out.setdefault(m.group(1), {"evidence": []})
            continue
        m = re.match(r"^\s*-\s*(evidence|level|why not [1-4]|check|mistake|check-files):\s*(.*?)\s*$", ln)
        if m and cur is not None:
            k, v = m.group(1), m.group(2)
            if k == "evidence":
                cur["evidence"].append(v)
            elif k not in cur:
                cur[k] = v[1:-1] if k == "check" and len(v) >= 2 and v[0] == v[-1] == "`" else v
    return out


def evidence(repo, item, added):
    """(problem or None, date or None) for one evidence line."""
    m = re.match(r"^added:(\d+)$", item)
    if m:
        hit = added.get(int(m.group(1)))
        return (None, hit[0]) if hit else (f"evidence {item} is not in {ADDED}; record it with M --add", None)
    m = FILE_LINE.match(item)
    if m:
        f, n = m.group(1).replace("\\", "/"), int(m.group(2))
        text = read_text(repo, f) if not not_product(f) else ""
        if not text:
            return f"evidence {item}: {f} is not a file in the repo", None
        if n < 1 or n > len(text.splitlines()):
            return f"evidence {item} is past the end of the file ({len(text.splitlines())} lines)", None
        return None, None
    if SHA.match(item):
        sha = commit_of(repo, item)
        return (None, commit_date(repo, sha)) if sha else (f"evidence {item} is not a commit in this repo", None)
    return f"evidence {item} is not a commit sha, a file:line or added:N", None


# ---------------- proofs ------------------------------------------------------
def copy_tree(repo, dest):
    def ignore(d, names):
        return [n for n in names if n in NOT_PRODUCT or n in NOT_PRODUCT_FILES or n.endswith(".pyc")]
    shutil.copytree(repo, dest, ignore=ignore)


def past_tree(repo, sha, dest):
    code, data, err = git(repo, "archive", "--format=tar", sha, binary=True)
    if code:
        raise OSError(err.decode("utf-8", "replace").strip())
    os.makedirs(dest)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        try:
            tar.extractall(dest, filter="data")
        except TypeError:
            tar.extractall(dest)


def run_cmd(cmd, cwd, timeout):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    # The agent writes commands in the shell it uses (`VAR=x cmd`, `&&`), so prefer bash.
    argv = [BASH, "-c", cmd] if BASH else cmd
    try:
        r = subprocess.run(argv, cwd=cwd, shell=not BASH, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return "timeout", "timed out"
    tail = [ln for ln in ((r.stdout or "") + (r.stderr or "")).replace(cwd, "<repo>").splitlines() if ln.strip()]
    return r.returncode, tail[-1][:160] if tail else ""


def prove(repo, cmd, mistake, check_files, timeout):
    """{"past": (exit, last line), "now": (exit, last line)}: cmd on the mistake commit with the check's
    files copied onto it, then on a copy of the working tree. The repo is never written."""
    tmp = tempfile.mkdtemp(prefix="mistake-")
    try:
        past = os.path.join(tmp, "past")
        past_tree(repo, mistake, past)
        for f in check_files:
            src = os.path.join(repo, *f.split("/"))
            if os.path.isfile(src):
                dst = os.path.join(past, *f.split("/"))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
        now = os.path.join(tmp, "now")
        copy_tree(repo, now)
        return {"past": run_cmd(cmd, past, timeout), "now": run_cmd(cmd, now, timeout)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------- the rule table and exceptions ------------------------------
def agent_files(repo, files):
    return [f for f in files if f in AGENT_FILES or f.startswith(".cursor/rules/")]


def read_table(repo, files):
    """(file or None, {class: {"rule", "level", "enforcer", "added"}}) from the first agent file with markers."""
    for f in agent_files(repo, files):
        text = read_text(repo, f)
        if OPEN_MARK in text and CLOSE_MARK in text.split(OPEN_MARK, 1)[1]:
            rows = {}
            for ln in text.split(OPEN_MARK, 1)[1].split(CLOSE_MARK, 1)[0].splitlines():
                cells = [c.strip() for c in ln.strip().strip("|").split("|")]
                if len(cells) < 5 or cells[0].lower() == "class" or set(cells[0]) <= set("-: "):
                    continue
                rows[cells[0]] = dict(zip(("rule", "level", "enforcer", "added"), cells[1:5]))
            return f, rows
    return None, {}


def draft_row(name, c):
    level = c.get("level", "")
    if level == "5":
        enforcer = "none"
    else:
        files = [x.strip() for x in c.get("check-files", "").split(",") if x.strip()]
        enforcer = files[0] if files else f"`{c.get('check', '')}`"
    return f"| {name} | [[fill: the rule, in one line]] | {level} | {enforcer} | {today()} |"


def exceptions(repo, files, names):
    problems = []
    for f in files:
        for i, ln in enumerate(read_text(repo, f).splitlines(), 1):
            m = re.search(r"mistake-ok:\s*(\S+)(.*)$", ln)
            if not m:
                continue
            fields = dict(re.findall(r"(\w+)=(.*?)(?=\s+\w+=|\s*$)", m.group(2)))
            where = f"{f}:{i}"
            if m.group(1) not in names:
                problems.append(f"{where}: the exception names {m.group(1)}, which is not a class in {CLASSES}")
            for k, why in (("reason", "why this line may break the rule"), ("expires", "a date, YYYY-MM-DD"),
                           ("approved", "the human who approved it; the agent never fills this")):
                if not fields.get(k, "").strip():
                    problems.append(f"{where}: the exception has no {k}=: {why}")
            exp = fields.get("expires", "").strip()
            if exp:
                if not re.match(r"^\d{4}-\d\d-\d\d$", exp):
                    problems.append(f"{where}: expires={exp} is not YYYY-MM-DD")
                elif exp < today():
                    problems.append(f"{where}: the exception expired on {exp}: remove it, or fix the line")
    return problems


# ---------------- the gate ----------------------------------------------------
def gate(repo, timeout=300):
    print('M = python "' + os.path.abspath(__file__) + '" ' + repo)
    files = product_files(repo)
    classes = read_classes(repo)
    added = read_added(repo)
    problems = {1: [], 2: [], 3: [], 4: []}
    bad = {name: False for name in classes}
    info = {name: {"dates": []} for name in classes}

    def flag(stage, name, text):
        problems[stage].append(f"{name}: {text}" if name else text)
        if name in bad:
            bad[name] = True

    # stage 1: each class has two pieces of evidence that exist
    if not classes:
        flag(1, None, f"no classes in {CLASSES}. Run M --mine, and group mistakes that happened twice")
    for name, c in classes.items():
        good = 0
        for item in c["evidence"]:
            why, date = evidence(repo, item, added)
            if why:
                flag(1, name, why)
            else:
                good += 1
                if date:
                    info[name]["dates"].append((date, item))
        if good < 2:
            flag(1, name, f"{good} piece(s) of evidence; a class needs 2 (a commit sha, a file:line, "
                          "or added:N from M --add)")

    # stage 2: a level, and why each stronger level did not work
    for name, c in classes.items():
        lv = c.get("level", "")
        if lv not in {"1", "2", "3", "4", "5"}:
            flag(2, name, "no `- level: N` (1 architecture, 2 types, 3 lint or CI check, 4 test, 5 docs only)")
            continue
        for k in range(1, int(lv)):
            if not c.get(f"why not {k}"):
                flag(2, name, f"level {lv} needs `- why not {k}:` saying why {LEVELS[k]} did not work")

    # stage 3: the check fails where the mistake is and passes now, and CI runs it
    ci = [f for f in files if CI_FILES.match(f)]
    ci_text = "\n".join(read_text(repo, f) for f in ci)
    for name, c in classes.items():
        if c.get("level") not in {"1", "2", "3", "4"}:
            continue
        cmd, mistake = c.get("check"), c.get("mistake")
        if not cmd:
            flag(3, name, "no `- check: `<command>``: a command that exits non-zero on the mistake")
        sha = commit_of(repo, mistake) if mistake else None
        if not mistake:
            flag(3, name, "no `- mistake: <sha>`: the commit where the mistake is present")
        elif not sha:
            flag(3, name, f"the mistake {mistake} is not a commit in this repo")
        check_files = [x.strip().replace("\\", "/") for x in c.get("check-files", "").split(",") if x.strip()]
        for f in check_files:
            if f not in files:
                flag(3, name, f"check-files {f} does not exist in the working tree")
        if not (cmd and sha):
            continue
        try:
            r = prove(repo, cmd, sha, check_files, timeout)
        except OSError as e:
            flag(3, name, f"could not rebuild {sha[:10]}: {e}")
            continue
        info[name]["proof"] = {"cmd": cmd, "mistake": sha, "past": list(r["past"]), "now": list(r["now"])}
        if r["past"][0] == 0:
            flag(3, name, f"`{cmd}` passes on {sha[:10]}, where the mistake is: it cannot fail. Make it catch "
                          "the mistake itself")
        if r["now"][0] != 0:
            flag(3, name, f"`{cmd}` fails on the working tree (exit {r['now'][0]}: {r['now'][1]}). Fix the "
                          "remaining uses; if old uses are already common, fail only on lines a change adds "
                          "(diff against the base), not on every old use")
        if ci and cmd not in ci_text:
            flag(3, name, f"`{cmd}` is not in the CI config ({', '.join(ci)}). Run the same command there")

    # stage 4: the rule table, repeats, and exceptions
    table_file, rows = read_table(repo, files)
    if table_file is None:
        draft = [draft_row(n, c) for n, c in classes.items()]
        write_file(repo, RULES_DRAFT, "\n".join([OPEN_MARK, "| Class | Rule | Level | Enforcer | Added |",
                                                 "|---|---|---|---|---|", *draft, CLOSE_MARK]) + "\n")
        problems[4].append(f"no rule table: add it to CLAUDE.md (or AGENTS.md) between `{OPEN_MARK}` and "
                           f"`{CLOSE_MARK}`; drafted in {RULES_DRAFT}:\n" + "\n".join(f"      {d}" for d in draft))
        for n in bad:
            bad[n] = True
    for name, c in classes.items() if table_file else ():
        if name not in rows:
            flag(4, name, f"no row in the rule table ({table_file}); add: {draft_row(name, c)}")
    for name, row in rows.items():
        c = classes.get(name, {})
        if c and row["level"] != c.get("level"):
            flag(4, name, f"the row says level {row['level']}, {CLASSES} says {c.get('level')}")
        enf = row["enforcer"].strip()
        if row["level"] == "5":
            if enf.lower() != "none":
                flag(4, name, f"a level-5 rule has nothing that fails; its enforcer is `none`, not {enf}")
        elif enf.startswith("`") and enf.endswith("`") and len(enf) > 1:
            if enf[1:-1] != c.get("check"):
                flag(4, name, f"the enforcer {enf} is not the class's check `{c.get('check')}`")
        elif not (enf in files or os.path.isdir(os.path.join(repo, enf))) or not_product(enf):
            flag(4, name, f"the enforcer {enf} does not exist. Name the check's file, or its command in backticks")
        if not re.match(r"^\d{4}-\d\d-\d\d$", row["added"]):
            flag(4, name, f"the row's added date `{row['added']}` is not YYYY-MM-DD")
        elif (row["level"] == "5" or enf.lower() == "none") and name in info:
            later = sorted(d for d in info[name]["dates"] if d[0] > row["added"])
            if later:
                flag(4, name, f"repeat: it happened again on {later[-1][0]} ({later[-1][1]}) after its rule was "
                              f"added on {row['added']}, and nothing enforces it. Fix it at level 1-4 in this change")
    problems[4] += exceptions(repo, files, set(classes))

    status = {}
    for name, c in classes.items():
        status[name] = "open" if bad[name] else "unenforced" if c.get("level") == "5" else "enforced"
    names = {1: "classes: two pieces of evidence each", 2: "level: the strongest fix that works",
             3: "proof: red on the mistake, green now", 4: "rules: a row per class that something enforces"}
    for g in (1, 2, 3, 4):
        print(f"STAGE {g} {names[g]}: " + ("holds" if not problems[g] else f"open, {len(problems[g])} to fix"))
        for line in problems[g]:
            print(f"  - {line}")
    print("\nCLASSES:")
    for name, c in classes.items():
        lv = c.get("level", "?")
        tail = f"level {lv}, nothing fails when it is skipped" if status[name] == "unenforced" else f"level {lv}"
        print(f"  {name}: {status[name]} ({tail})")
    ledger = {"shas": shas(repo), "ci": ci,
              "classes": {n: {"status": status[n], "level": classes[n].get("level"), **info[n]} for n in classes}}
    with open(os.path.join(repo, LEDGER), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(ledger, fh, indent=1, sort_keys=True)
    if not problems[1] and not problems[2]:
        text = draft_answer(classes, ledger)
        write_file(repo, ANSWER, text)
        print(f"\nANSWER (drafted in {ANSWER}; fill its slots, then M --answer-check {ANSWER}):\n")
        print(text)
    open_stages = [g for g in (1, 2, 3, 4) if problems[g]]
    if open_stages:
        print(f"MISTAKE-GATE: open({', '.join(map(str, open_stages))}): fix the lines above, then M --gate")
        return 1
    n_enf = sum(s == "enforced" for s in status.values())
    print(f"MISTAKE-GATE: done({len(classes)} classes, {n_enf} enforced, {len(classes) - n_enf} unenforced)")
    return 0


def draft_answer(classes, ledger):
    st = {n: v["status"] for n, v in ledger["classes"].items()}
    counts = {s: sum(v == s for v in st.values()) for s in ("enforced", "unenforced", "open")}
    lines = ["# Mistake proof", "",
             f"Classes: {len(classes)} ({counts['enforced']} enforced, {counts['unenforced']} unenforced, "
             f"{counts['open']} open)",
             "CI: " + (", ".join(ledger["ci"]) if ledger["ci"] else "no CI config found; checks run locally only")]
    for name, c in classes.items():
        lv = int(c["level"])
        rec = ledger["classes"][name]
        lines += ["", f"## {name}", f"Status: {st[name]}", f"Level: {lv} ({LEVELS[lv]})",
                  "Evidence: " + ", ".join(c["evidence"])]
        if lv > 1:
            lines.append("Why not stronger: " + "; ".join(f"{k} {LEVELS[k]}: {c[f'why not {k}']}"
                                                         for k in range(1, lv)))
        p = rec.get("proof")
        if p and st[name] == "enforced":
            lines.append(f"Proof: `{p['cmd']}` failed on {p['mistake'][:10]} (exit {p['past'][0]}) "
                         "and passed on the working tree")
        if lv < 5:
            lines.append("Fix: [[fill: what changed in the repo so the next agent cannot make this mistake]]")
        else:
            lines.append("Unenforced: [[fill: the judgment call that keeps this in docs]]")
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
        print("ANSWER-CHECK: refused\n  - the gate has recorded nothing. Run M --gate first")
        return 1
    problems = []
    rel_answer = os.path.relpath(os.path.abspath(path), repo).replace(os.sep, "/")
    now = {f: s for f, s in shas(repo).items() if f != rel_answer}
    then = {f: s for f, s in ledger["shas"].items() if f != rel_answer}
    moved = sorted(f for f in set(now) | set(then) if now.get(f) != then.get(f))
    if moved:
        problems.append(f"the code changed since the last gate ({', '.join(moved[:4])}). Run M --gate again")
    if FILL in text:
        problems.append("unfilled [[fill: ...]] slot(s): write what each asks")
    recorded = ledger["classes"]
    seen = set()
    for m in re.finditer(r"(?m)^##\s+(\S+)\s*\n((?:(?!##\s).*\n?)*)", text):
        name, body = m.group(1), m.group(2)
        seen.add(name)
        rec = recorded.get(name)
        if rec is None or rec["status"] == "open":
            problems.append(f"names {name}, a class the gate did not clear")
            continue
        s = re.search(r"(?im)^\s*Status:\s*(\w+)", body)
        if s and s.group(1).lower() != rec["status"]:
            problems.append(f"calls {name} {s.group(1).lower()}, but the gate recorded it {rec['status']}"
                            + (" (level 5: nothing fails when it is skipped)" if rec["status"] == "unenforced" else ""))
    for name, rec in recorded.items():
        if rec["status"] != "open" and name not in seen:
            problems.append(f"leaves out {name}; copy its section from {ANSWER}")
    if problems:
        print("ANSWER-CHECK: refused")
        print("".join(f"  - {p}\n" for p in problems), end="")
        return 1
    n_enf = sum(r["status"] == "enforced" for r in recorded.values())
    print(f"ANSWER OK ({len(recorded)} classes, {n_enf} enforced)")
    return 0


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description="Turn a repeated agent mistake into a check that fails.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--mine", action="store_true", help="list candidate mistakes from history")
    ap.add_argument("--since", help="with --mine: only commits after this ref")
    ap.add_argument("--add", metavar="TEXT", help="record a correction the operator gave")
    ap.add_argument("--gate", action="store_true", help="check the stages and draft the reply")
    ap.add_argument("--answer-check", metavar="FILE", help="refuse a reply the gate's record does not back")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per check run")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo)
    if a.answer_check:
        return answer_check(repo, a.answer_check)
    if a.add:
        return add(repo, a.add)
    if a.mine:
        code = mine(repo, a.since)
        if code or not a.gate:
            return code
        print()
    if a.gate:
        return gate(repo, a.timeout)
    print("M --mine lists candidates; M --add records a correction; M --gate checks the stages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
