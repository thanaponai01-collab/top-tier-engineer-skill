#!/usr/bin/env python3
"""release.py - the mechanical side of the safe-release skill.

A model that reads the code well writes a sound migration and a plausible way back. What it skips is
running the way back: the old code against the migrated data (the deploy window, and the state a
"revert" leaves), the down step on a copy of the real data compared row for row, the constraints the
change dropped. This runs all of that on throwaway copies and never on the live data.

  R                         the live data found, the code that runs today, what changed, what is recorded
  R --rehearse --forward CMD [--back CMD] --probe CMD [--probe ...] [--old REF|DIR]
                            on throwaway copies of the repo and its live data:
                              the probes on today's code and today's data (the baseline)
                              forward on the changed code; forward again (rerun-safe)
                              the probes on the changed code, and on today's code (the deploy window
                              and a code-only revert both run old code on the migrated data)
                              back after forward; the data compared with the baseline row for row;
                              the probes on today's code after the way back
  R --gate                  check the stages and print every problem with its fix:
    1 forward   the change was rehearsed on the current tree: forward and its rerun pass, the changed
                code's probes pass, a probe writes, and every constraint the change drops is named
    2 back      today's code runs on the migrated data (or the window is closed by downtime), the way
                back runs, and it gives the data back, or every loss is named with the step that loses it
    3 call      .release/plan.md says ship/stage/hold, the rollback in one sentence, the point of no
                return and what to watch, accounts for every file the release carries, and the live
                data is as it was when the work started

`R` is `python release.py <repo>`. Stdlib only.
"""
import argparse, hashlib, json, os, re, shutil, sqlite3, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _encoding import utf8_streams  # noqa: E402

STATE = ".release"
BEFORE = f"{STATE}/before"
LEDGER = f"{STATE}/state.json"
PLAN = f"{STATE}/plan.md"
FILL = "[[fill"
NOT_PRODUCT = {".git", "__pycache__", "node_modules", ".venv", "venv", STATE, ".debug", ".wire", ".latent",
               ".features", ".structure", ".threat", ".verify-state-cache", ".pytest_cache", ".mypy_cache",
               ".ruff_cache", ".evolve", ".perf"}
NOT_PRODUCT_FILES = {".verify-state.json"}
SQLITE_MAGIC = b"SQLite format 3\x00"
BASH = shutil.which("bash")
CALLS = {"ship", "stage", "hold"}
PLAN_KEYS = ["CALL", "ROLLBACK", "NO-RETURN", "WATCH"]


# ---------------- files ----------------------------------------------------------
def rel(path, root):
    return os.path.relpath(path, root).replace(os.sep, "/")


def walk_files(root):
    for d, subdirs, names in os.walk(root):
        subdirs[:] = sorted(s for s in subdirs if s not in NOT_PRODUCT)
        for n in sorted(names):
            if n not in NOT_PRODUCT_FILES and not n.endswith(".pyc"):
                yield os.path.join(d, n)


def is_sqlite(path):
    try:
        with open(path, "rb") as fh:
            return fh.read(16) == SQLITE_MAGIC
    except OSError:
        return False


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def code_sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()[:16]


def find_data(repo, named=()):
    """The live data: every SQLite file outside tests, plus files named with --data."""
    found = set()
    for p in walk_files(repo):
        r = rel(p, repo)
        if r.split("/")[0] in ("tests", "test"):
            continue
        if is_sqlite(p):
            found.add(r)
    for n in named:
        if os.path.isfile(os.path.join(repo, n)):
            found.add(rel(os.path.join(repo, n), repo))
    return sorted(found)


def product_files(root, data):
    """{rel: sha} for the code and docs: everything but the live data and tools' state."""
    return {rel(p, root): code_sha(p) for p in walk_files(root) if rel(p, root) not in data}


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def save(repo, ledger):
    path = os.path.join(repo, LEDGER)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(ledger, fh, indent=1, sort_keys=True)


def load(repo):
    return read_json(os.path.join(repo, LEDGER), {})


# ---------------- the code that runs today ---------------------------------------
def git(repo, *args):
    try:
        p = subprocess.run(["git", *args], cwd=repo, capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return p.stdout if p.returncode == 0 else None


def materialize_old(repo, ledger, dest):
    """Write the code that runs today into DEST. (description, error)."""
    src = ledger.get("old")
    if src and src.get("kind") == "git":
        tar = git(repo, "archive", "--format=tar", src["ref"])
        if tar is None:
            return None, f"git archive {src['ref']} failed"
        import io, tarfile
        os.makedirs(dest, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
            tf.extractall(dest, filter="data") if sys.version_info >= (3, 12) else tf.extractall(dest)
        return f"git {src['ref']}", None
    if src and src.get("kind") == "dir":
        base = src["path"] if os.path.isabs(src["path"]) else os.path.join(repo, src["path"])
        if not os.path.isdir(base):
            return None, f"{src['path']} is gone"
        shutil.copytree(base, dest, ignore=shutil.ignore_patterns(*NOT_PRODUCT, "*.pyc"))
        return src["path"], None
    return None, "no record of the code that runs today"


def pick_old(repo, ledger, old_arg, data):
    """Decide where today's code comes from, once: --old, else git HEAD, else a snapshot of the tree now."""
    if old_arg:
        if os.path.isdir(os.path.join(repo, old_arg)) or os.path.isdir(old_arg):
            ledger["old"] = {"kind": "dir", "path": old_arg}
        elif git(repo, "rev-parse", "--verify", old_arg + "^{commit}") is not None:
            ledger["old"] = {"kind": "git", "ref": old_arg}
        else:
            return f"--old {old_arg} is neither a folder nor a git commit"
        return None
    if ledger.get("old"):
        return None
    if git(repo, "rev-parse", "--verify", "HEAD^{commit}") is not None:
        ledger["old"] = {"kind": "git", "ref": "HEAD"}
        return None
    before = os.path.join(repo, BEFORE)
    if not os.path.isdir(before):
        shutil.copytree(repo, before, ignore=shutil.ignore_patterns(*NOT_PRODUCT, "*.pyc", *[os.path.basename(d) for d in data]))
    ledger["old"] = {"kind": "dir", "path": BEFORE}
    ledger["old_note"] = "no git: the tree as it was at the first R call is taken as the code that runs today"
    return None


def first_touch(repo, ledger, data):
    """Fingerprint the live data the first time R sees it, so the gate can tell it was never touched."""
    seen = ledger.setdefault("live", {})
    for d in data:
        if d not in seen:
            seen[d] = sha(os.path.join(repo, d))


# ---------------- running on copies ---------------------------------------------
def clean_env(repo):
    """The environment, minus any variable that points into the real repo (it could aim at the live data)."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    real = os.path.normcase(os.path.abspath(repo))
    for k, v in list(env.items()):
        if real in os.path.normcase(v):
            del env[k]
    return env


def run(cmd, cwd, env, timeout):
    """Run CMD in a tree copy, with the tree's root importable (a probe in .release/probes/ imports `app`)."""
    env = dict(env, PYTHONPATH=os.pathsep.join([cwd] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])))
    argv = [BASH, "-c", cmd] if BASH else cmd
    try:
        p = subprocess.run(argv, cwd=cwd, shell=not BASH, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=env)
        return p.returncode, ((p.stdout or "") + (p.stderr or "")).replace(cwd, "<copy>")
    except subprocess.TimeoutExpired:
        return "timeout", "timed out"


def put_data(tree, data_dir, data):
    for d in data:
        dest = os.path.join(tree, *d.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        src = os.path.join(data_dir, *d.split("/"))
        if os.path.exists(src):
            shutil.copyfile(src, dest)
        elif os.path.exists(dest):
            os.remove(dest)


def take_data(tree, data_dir, data):
    for d in data:
        src = os.path.join(tree, *d.split("/"))
        dest = os.path.join(data_dir, *d.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.exists(src):
            shutil.copyfile(src, dest)


def tail(text, n=4):
    return [ln[:200] for ln in text.splitlines() if ln.strip()][-n:]


# ---------------- reading data ---------------------------------------------------
def snapshot(data_dir, data):
    """{file: {"tables": {name: {"sql", "cols", "rows"}}, "indexes": [...]}} or {"bytes": sha}."""
    out = {}
    for d in data:
        p = os.path.join(data_dir, *d.split("/"))
        if not os.path.exists(p):
            out[d] = None
            continue
        if not is_sqlite(p):
            out[d] = {"bytes": sha(p)}
            continue
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        try:
            tables, indexes = {}, []
            for name, sql in conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' "
                                          "AND name NOT LIKE 'sqlite_%' ORDER BY name"):
                info = list(conn.execute(f'PRAGMA table_info("{name}")'))
                cols = [c[1] for c in info]
                rows = [list(r) for r in conn.execute(f'SELECT * FROM "{name}"')]
                tables[name] = {"sql": sql or "", "cols": cols, "rows": rows,
                                "notnull": sorted(c[1] for c in info if c[3]),
                                "unique": unique_sets(conn, name)}
            for name, tbl, sql in conn.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index'"):
                indexes.append([tbl, name, sql or ""])
            out[d] = {"tables": tables, "indexes": sorted(indexes)}
        finally:
            conn.close()
    return out


def unique_sets(conn, table):
    """Column sets that must be unique: UNIQUE constraints, unique indexes, the primary key."""
    sets = []
    for idx in conn.execute(f'PRAGMA index_list("{table}")'):
        if idx[2]:
            cols = [c[2] for c in conn.execute(f'PRAGMA index_info("{idx[1]}")')]
            sets.append(",".join(cols))
    return sorted(set(sets))


def keyed(table):
    cols, rows = table["cols"], table["rows"]
    key = "id" if "id" in cols else None
    if key:
        i = cols.index(key)
        return {r[i]: dict(zip(cols, r)) for r in rows}
    return {json.dumps(r, sort_keys=True, default=str): dict(zip(cols, r)) for r in rows}


def norm(v):
    return round(v, 9) if isinstance(v, float) else v


def compare(a, b, ignore=("schema_version", "schema_migrations", "alembic_version", "django_migrations")):
    """Differences that matter between two snapshots, as plain lines (empty = the same data)."""
    lines = []
    for f in sorted(set(a) | set(b)):
        x, y = a.get(f), b.get(f)
        if x == y:
            continue
        if x is None or y is None or "bytes" in (x or {}) or "bytes" in (y or {}):
            lines.append(f"{f}: {'appeared' if x is None else 'is gone' if y is None else 'changed'}")
            continue
        for t in sorted(set(x["tables"]) | set(y["tables"])):
            if t in ignore:
                continue
            tx, ty = x["tables"].get(t), y["tables"].get(t)
            if tx is None:
                lines.append(f"{f}: table {t} is new ({len(ty['rows'])} rows)")
                continue
            if ty is None:
                lines.append(f"{f}: table {t} is gone ({len(tx['rows'])} rows with it)")
                continue
            gone = [c for c in tx["cols"] if c not in ty["cols"]]
            new = [c for c in ty["cols"] if c not in tx["cols"]]
            if gone:
                filled = {c: sum(1 for r in tx["rows"] if r[tx["cols"].index(c)] not in (None, "")) for c in gone}
                lines.append(f"{f}: {t} lost column(s) " + ", ".join(f"{c} ({filled[c]} filled values)" for c in gone))
            if new:
                lines.append(f"{f}: {t} has new column(s) {', '.join(new)}")
            kx, ky = keyed(tx), keyed(ty)
            missing, added = [k for k in kx if k not in ky], [k for k in ky if k not in kx]
            shared = [c for c in tx["cols"] if c in ty["cols"]]
            changed = [k for k in kx if k in ky and any(norm(kx[k][c]) != norm(ky[k][c]) for c in shared)]
            if missing:
                lines.append(f"{f}: {t} lost {len(missing)} row(s), e.g. {short(kx[missing[0]])}")
            if added:
                lines.append(f"{f}: {t} has {len(added)} extra row(s), e.g. {short(ky[added[0]])}")
            if changed:
                k = changed[0]
                diff = {c: [kx[k][c], ky[k][c]] for c in shared if norm(kx[k][c]) != norm(ky[k][c])}
                lines.append(f"{f}: {t} has {len(changed)} changed row(s), e.g. id {k}: "
                             + ", ".join(f"{c} {v[0]!r} -> {v[1]!r}" for c, v in list(diff.items())[:3]))
            for kind, label in (("unique", "unique on"), ("notnull", "NOT NULL on")):
                lost = [s for s in tx[kind] if s not in ty[kind] and all(c in ty["cols"] for c in s.split(","))]
                if lost:
                    lines.append(f"{f}: {t} lost {label} {', '.join(lost)}")
    return lines


def dropped_constraints(a, b):
    """Constraints a forward step drops on columns that are still there: (file, table, what)."""
    out = []
    for f in sorted(set(a) & set(b)):
        x, y = a[f], b[f]
        if not x or not y or "tables" not in x or "tables" not in y:
            continue
        for t, tx in x["tables"].items():
            ty = y["tables"].get(t)
            if not ty:
                continue
            for s in tx["unique"]:
                if s not in ty["unique"] and all(c in ty["cols"] for c in s.split(",")) and s != "id":
                    out.append(f"{f}: {t} unique on {s}")
            for c in tx["notnull"]:
                if c not in ty["notnull"] and c in ty["cols"]:
                    out.append(f"{f}: {t} NOT NULL on {c}")
    return out


def required_new(a, b):
    """New NOT NULL columns with no default: an INSERT written before the change fails on them."""
    out = []
    for f in sorted(set(a) & set(b)):
        x, y = a[f], b[f]
        if not x or not y or "tables" not in x or "tables" not in y:
            continue
        for t, ty in y["tables"].items():
            tx = x["tables"].get(t)
            if not tx:
                continue
            for c in ty["cols"]:
                if c not in tx["cols"] and c in ty["notnull"] and not has_default(ty["sql"], c):
                    out.append(f"{f}: {t}.{c}")
    return out


def has_default(sql, col):
    m = re.search(r'["`\[]?\b' + re.escape(col) + r'\b["`\]]?\s+[^,]*', sql, re.IGNORECASE)
    return bool(m and re.search(r"\bDEFAULT\b", m.group(0), re.IGNORECASE))


def short(row):
    text = ", ".join(f"{k}={v!r}" for k, v in list(row.items())[:4])
    return "{" + (text[:120] + "..." if len(text) > 120 else text) + "}"


def samples(a, b, n=4):
    """A few changed rows from each table the forward step touched: only the columns that moved,
    before -> after, spread across the table, a row whose old value was empty first."""
    out = []
    for f in sorted(set(a) & set(b)):
        x, y = a[f], b[f]
        if not x or not y or "tables" not in x or "tables" not in y:
            continue
        for t in sorted(set(x["tables"]) & set(y["tables"])):
            if t in ("schema_version", "schema_migrations"):
                continue
            kx, ky = keyed(x["tables"][t]), keyed(y["tables"][t])
            changed = [k for k in kx if k in ky and kx[k] != ky[k]]
            if not changed:
                continue
            moved = sorted({c for k in changed for c in set(kx[k]) | set(ky[k]) if kx[k].get(c) != ky[k].get(c)})
            out.append(f"{f}: {t}, {len(changed)} of {len(kx)} rows changed ({', '.join(moved)}):")
            pick = [k for k in changed if any(kx[k].get(c) in (None, "") for c in moved)][:1]
            step = max(1, len(changed) // n)
            pick += [k for k in changed[::step] if k not in pick][:n - len(pick)]
            for k in pick:
                same = ", ".join(f"{c}={v!r}" for c, v in kx[k].items() if c not in moved and c != "id")
                moves = ", ".join(f"{c}: {kx[k].get(c, '(none)')!r} -> {ky[k].get(c, '(none)')!r}" for c in moved)
                out.append(f"    id {k}: {moves}   [{same[:100]}]")
    return out


def probe_files(repo, cmd):
    """Repo files a probe command names (`python probe.py`, `tests/test_x.py`, `-m tests.test_x`)."""
    found = []
    for t in re.split(r"[\s;&|<>()]+", cmd):
        t = t.strip("'\"").split("::")[0]
        if not t or t.startswith("-"):
            continue
        cands = [t] + ([t.replace(".", "/") + ".py"] if re.match(r"^[A-Za-z_][\w.]*$", t) else [])
        for c in cands:
            p = os.path.join(repo, *c.split("/"))
            if os.path.isfile(p):
                found.append(rel(p, repo))
                break
    return found


# ---------------- stage work: the rehearsal --------------------------------------
def rehearse(repo, forward, back, probes, old_arg, data_named, timeout):
    if not forward:
        print('REHEARSE: give the forward step: R --rehearse --forward "<cmd that applies the change to the data>" '
              '--probe "<cmd that uses the data through the code>" [--back "<cmd that undoes it>"]')
        return 2
    if not probes:
        print("REHEARSE: give at least one --probe: a command that reads and writes the data through the code "
              "(a smoke script, the CLI, a request handler called directly). It is run on today's code and on "
              "the changed code, before and after each step, so it is what tells the states apart.")
        return 2
    ledger = load(repo)
    data = find_data(repo, (ledger.get("data_named") or []) + list(data_named))
    ledger["data_named"] = sorted(set((ledger.get("data_named") or []) + list(data_named)))
    if not data:
        print("REHEARSE: no live data found (no SQLite file outside tests/). Name it with --data PATH.")
        return 2
    err = pick_old(repo, ledger, old_arg, data)
    if err:
        print("REHEARSE: " + err)
        return 2
    first_touch(repo, ledger, data)
    live_before = {d: sha(os.path.join(repo, d)) for d in data}
    env = clean_env(repo)
    tmp = tempfile.mkdtemp(prefix="release-")
    rec = {"forward": forward, "back": back, "probes": probes, "data": data, "problems": [], "notes": []}
    try:
        new = os.path.join(tmp, "new")
        old = os.path.join(tmp, "old")
        shutil.copytree(repo, new, ignore=shutil.ignore_patterns(*NOT_PRODUCT, "*.pyc"))
        desc, err = materialize_old(repo, ledger, old)
        if err:
            print("REHEARSE: " + err)
            return 2
        rec["old"] = desc
        for p in probes:   # a probe script written for the rehearsal (.release/probes/ is fine) runs on both trees
            for f in probe_files(repo, p):
                for tree in (new, old):
                    dest = os.path.join(tree, *f.split("/"))
                    if not os.path.exists(dest):
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        shutil.copyfile(os.path.join(repo, *f.split("/")), dest)
        states = {k: os.path.join(tmp, "data-" + k) for k in ("live", "fwd", "fwd2", "back")}
        os.makedirs(states["live"])
        take_data(repo, states["live"], data)
        s0 = snapshot(states["live"], data)

        def probe_all(tree, state, label):
            start = snapshot(state, data)
            results = []
            for p in probes:
                put_data(tree, state, data)   # each probe starts from the same data
                code, out = run(p, tree, env, timeout)
                seen = os.path.join(tmp, "probe-" + label)
                shutil.rmtree(seen, ignore_errors=True)
                take_data(tree, seen, data)
                results.append({"probe": p, "exit": code, "tail": tail(out, 3), "out": out[-4000:],
                                "wrote": bool(compare(start, snapshot(seen, data), ignore=()))})
            rec[label] = [{k: v for k, v in r.items() if k != "out"} for r in results]
            return results

        def step(cmd, tree, src, dst, label):
            put_data(tree, src, data)
            code, out = run(cmd, tree, env, timeout)
            os.makedirs(dst, exist_ok=True)
            take_data(tree, dst, data)
            rec[label] = {"cmd": cmd, "exit": code, "tail": tail(out, 4)}
            return code, out

        base = probe_all(old, states["live"], "probes_today")
        rec["probe_writes"] = [r["wrote"] for r in base]

        code, out = step(forward, new, states["live"], states["fwd"], "forward_run")
        s1 = snapshot(states["fwd"], data)
        rec["forward_changes"] = compare(s0, s1)
        rec["samples"] = samples(s0, s1)
        rec["dropped"] = dropped_constraints(s0, s1)
        rec["required_new"] = required_new(s0, s1)
        code2, _ = step(forward, new, states["fwd"], states["fwd2"], "forward_again")
        rec["rerun_diff"] = compare(s1, snapshot(states["fwd2"], data), ignore=())
        rec["probes_new"] = None
        if code == 0:
            probe_all(new, states["fwd"], "probes_new")
            probe_all(old, states["fwd"], "probes_window")
            if back:
                bcode, _ = step(back, new, states["fwd"], states["back"], "back_run")
                if bcode == 0:
                    s2 = snapshot(states["back"], data)
                    rec["back_diff"] = compare(s0, s2)
                    after = probe_all(old, states["back"], "probes_after_back")
                    rec["probe_output_changed"] = [p for p, a, b in zip(probes, base, after)
                                                   if a["exit"] == 0 and b["exit"] == 0 and a["out"] != b["out"]]
        rec["tree"] = product_files(repo, data)
        live_after = {d: sha(os.path.join(repo, d)) for d in data}
        rec["live_touched"] = [d for d in data if live_after[d] != live_before[d]]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ledger["rehearsal"] = rec
    save(repo, ledger)
    show_rehearsal(rec)
    print("next: R --gate")
    return 0


def show_rehearsal(rec):
    print(f"REHEARSAL on copies of {', '.join(rec['data'])}; today's code from {rec.get('old')}")

    def probes_line(label, title):
        rs = rec.get(label)
        if rs is None:
            return
        bad = [r for r in rs if r["exit"] != 0]
        print(f"  {title}: " + ("all pass" if not bad else f"{len(bad)} of {len(rs)} fail"))
        for r in bad:
            print(f"    `{r['probe']}` exit {r['exit']}: {' / '.join(r['tail'][-2:])}")
    probes_line("probes_today", "probes on today's code, today's data")
    f = rec.get("forward_run") or {}
    print(f"  forward `{f.get('cmd')}`: exit {f.get('exit')}" + ("" if f.get("exit") == 0 else
                                                                 f"  {' / '.join(f.get('tail', [])[-2:])}"))
    for line in rec.get("forward_changes", [])[:12]:
        print(f"    {line}")
    for line in rec.get("samples", [])[:10]:
        print(f"    {line}")
    g = rec.get("forward_again") or {}
    if g:
        print(f"  forward again: exit {g.get('exit')}" + ("" if not rec.get("rerun_diff") else
                                                          f", data changed again: {rec['rerun_diff'][0]}"))
    probes_line("probes_new", "probes on the changed code, migrated data")
    probes_line("probes_window", "probes on today's code, migrated data (deploy window, code-only revert)")
    b = rec.get("back_run")
    if b:
        print(f"  back `{b['cmd']}`: exit {b['exit']}" + ("" if b["exit"] == 0 else f"  {' / '.join(b['tail'][-2:])}"))
        if "back_diff" in rec:
            print("    data after back: " + ("the same as today's" if not rec["back_diff"] else "differs:"))
            for line in rec["back_diff"][:10]:
                print(f"      {line}")
        probes_line("probes_after_back", "probes on today's code after the way back")
    for line in rec.get("dropped", []):
        print(f"  constraint dropped by forward: {line}")
    for line in rec.get("required_new", []):
        print(f"  new NOT NULL column with no default (an INSERT written before the change fails): {line}")
    if rec.get("live_touched"):
        print(f"  !! the live data changed while the rehearsal ran: {', '.join(rec['live_touched'])}")


# ---------------- the plan --------------------------------------------------------
def read_plan(repo):
    try:
        with open(os.path.join(repo, PLAN), encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return {}, {}, {}, ""
    keys, carries, named = {}, {}, {"DROPS": [], "LOSES": []}
    for line in text.splitlines():
        m = re.match(r"^\s*-?\s*(CALL|ROLLBACK|NO-RETURN|WATCH|WINDOW)\s*:\s*(.*)$", line, re.IGNORECASE)
        if m:
            keys[m.group(1).upper()] = m.group(2).strip()
            continue
        m = re.match(r"^\s*-\s*CARRIES\s+`?([^`:]+?)`?\s*:\s*(.*)$", line)
        if m:
            carries[m.group(1).strip()] = m.group(2).strip()
            continue
        m = re.match(r"^\s*-\s*(DROPS|LOSES)\s+(.*)$", line)
        if m:
            named[m.group(1)].append(m.group(2).strip())
    return keys, carries, named, text


def reason_for(named, kind, what):
    """The reason after `- KIND <what>:` in the plan, or ''. WHAT may hold colons itself."""
    for entry in named.get(kind, []):
        if entry.startswith(what + ":"):
            return entry[len(what) + 1:].strip()
    return ""


def loss_label(line):
    """A stable name for one loss the way back leaves: the line without its example."""
    return line.split(", e.g.")[0].strip()


def append_plan(repo, lines):
    if not lines:
        return 0
    path = os.path.join(repo, PLAN)
    exists = os.path.exists(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        if not exists:
            fh.write("# Release plan\n\nThe gate reads these lines. Replace each [[fill: ...]] with the answer.\n\n")
        fh.write("\n".join(lines) + "\n")
    return len(lines)


def filled(v):
    return bool(v) and not v.startswith(FILL)


def first_word(v):
    m = re.match(r"^\W*(\w+)", v or "")
    return m.group(1).lower() if m else ""


def is_test_or_doc(r):
    """Tests and prose ship with the release but change nothing in production."""
    parts = r.split("/")
    return (any(p in ("tests", "test", "docs") for p in parts[:-1])
            or re.match(r"^(test_.+|.+_test|conftest)\.py$", parts[-1]) is not None
            or os.path.splitext(r)[1].lower() in (".md", ".rst", ".txt"))


def changed_files(repo, ledger, data):
    """Product files that differ from the code that runs today: what the release carries."""
    tmp = tempfile.mkdtemp(prefix="release-old-")
    try:
        old = os.path.join(tmp, "old")
        _, err = materialize_old(repo, ledger, old)
        if err:
            return None
        was, now = product_files(old, data), product_files(repo, data)
        return sorted(f for f in set(was) | set(now) if was.get(f) != now.get(f) and not is_test_or_doc(f))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------- the gate --------------------------------------------------------
def gate(repo):
    ledger = load(repo)
    rec = ledger.get("rehearsal")
    data = find_data(repo, ledger.get("data_named") or [])
    problems = {1: [], 2: [], 3: []}
    print('R = python "' + os.path.abspath(__file__) + '" ' + repo)
    keys, carries, named, text = read_plan(repo)
    if not rec:
        problems[1].append('nothing rehearsed. R --rehearse --forward "<cmd>" --back "<cmd>" --probe "<cmd>" '
                           "runs it all on copies of the live data")
    else:
        if rec.get("tree") != product_files(repo, rec["data"]):
            problems[1].append("the code changed since the rehearsal: rehearse again so the record is this tree's")
        bad_today = [r for r in rec.get("probes_today", []) if r["exit"] != 0]
        for r in bad_today:
            problems[1].append(f"probe `{r['probe']}` fails on today's code and today's data (exit {r['exit']}): "
                               "a probe must work before the change, or it cannot show what the change breaks")
        if not any(rec.get("probe_writes", [])):
            problems[1].append("no probe writes to the data: the code that runs during and after the release also "
                               "writes, and a read-only rehearsal cannot see an INSERT the change breaks. Add a probe "
                               "that writes the way the product does")
        f = rec.get("forward_run") or {}
        if f.get("exit") != 0:
            problems[1].append(f"forward `{f.get('cmd')}` fails on a copy of the live data (exit {f.get('exit')}): "
                               + " / ".join(f.get("tail", [])[-2:]))
        elif not rec.get("forward_changes"):
            problems[1].append("forward changed nothing in the data: check that it runs against the copy's data "
                               "(a path or variable may point elsewhere)")
        g = rec.get("forward_again") or {}
        if f.get("exit") == 0 and (g.get("exit") != 0 or rec.get("rerun_diff")):
            problems[1].append("forward is not safe to run twice: " + (f"exit {g.get('exit')} the second time"
                               if g.get("exit") != 0 else rec["rerun_diff"][0])
                               + ". A deploy that is retried after a timeout runs it again")
        for r in rec.get("probes_new") or []:
            if r["exit"] != 0:
                problems[1].append(f"probe `{r['probe']}` fails on the changed code with the migrated data "
                                   f"(exit {r['exit']}): {' / '.join(r['tail'][-2:])}")
        for d in rec.get("dropped", []):
            if not filled(reason_for(named, "DROPS", d)):
                problems[1].append(f"forward drops a constraint: {d}. Keep it, or add `- DROPS {d}: <why the data "
                                   f"no longer needs it>` to {PLAN}")

        window = keys.get("WINDOW", "")
        for r in rec.get("probes_window") or []:
            if r["exit"] != 0 and not filled(window):
                problems[2].append(f"today's code fails on the migrated data: `{r['probe']}` exit {r['exit']} "
                                   f"({' / '.join(r['tail'][-2:])}). Between the migration and the restart, and after "
                                   "a code-only revert, today's code runs on this data. Make the change additive "
                                   f"(expand now, contract in a later release), or close the window with downtime and "
                                   f"say so: `WINDOW: <how no old code runs on the new data>` in {PLAN}")
        for c in rec.get("required_new", []):
            if not filled(window) and not any(r["exit"] != 0 for r in rec.get("probes_window") or []):
                problems[2].append(f"new NOT NULL column with no default: {c}. Today's INSERTs that leave it out "
                                   "fail; no probe here caught it, so add one that inserts the way today's code does, "
                                   "or give the column a default")
        b = rec.get("back_run")
        if not rec.get("back"):
            problems[2].append("no way back rehearsed: add --back \"<cmd that undoes the change>\" and rehearse again. "
                               "A revert of the code alone leaves the data as forward made it")
        elif not b or b.get("exit") != 0:
            problems[2].append(f"back `{rec['back']}` fails after forward on a copy (exit {(b or {}).get('exit')}): "
                               + " / ".join((b or {}).get("tail", [])[-2:]))
        else:
            for line in rec.get("back_diff", []):
                label = loss_label(line)
                if not filled(reason_for(named, "LOSES", label)):
                    problems[2].append(f"the way back does not give the data back: {line}. Make back restore it, or "
                                       f"name the loss: `- LOSES {label}: <the step after which it is lost, and what>` "
                                       f"in {PLAN}")
            for r in rec.get("probes_after_back") or []:
                if r["exit"] != 0:
                    problems[2].append(f"after the way back, today's code fails: `{r['probe']}` exit {r['exit']} "
                                       f"({' / '.join(r['tail'][-2:])})")
        if rec.get("live_touched"):
            problems[3].append(f"the live data changed while the rehearsal ran: {', '.join(rec['live_touched'])}. "
                               "Something in the commands reached it; find what before anything else")

    # stage 3: the call
    slots = [f"{k}: [[fill: {hint}]]" for k, hint in (
        ("CALL", "ship, stage or hold, and the biggest risk"),
        ("ROLLBACK", "the way back in one sentence, the commands in order"),
        ("NO-RETURN", "the step after which going back loses data, and what is lost; or none"),
        ("WATCH", "1-3 signals that point at this change, and the level that triggers the rollback"))
        if k not in keys]
    carried = changed_files(repo, ledger, data) if ledger.get("old") else None
    if carried:
        slots += [f"- CARRIES {c}: [[fill: what it changes in production]]" for c in carried if c not in carries]
    added = append_plan(repo, slots)
    if added:
        keys, carries, named, text = read_plan(repo)
        print(f"(appended {added} line{'s' if added != 1 else ''} to {PLAN})")
    for k in PLAN_KEYS:
        if not filled(keys.get(k, "")):
            problems[3].append(f"{PLAN}: {k} is not filled")
    call = first_word(keys["CALL"]) if filled(keys.get("CALL", "")) else ""
    if call and call not in CALLS:
        problems[3].append(f"{PLAN}: CALL starts with ship, stage or hold, not {call!r}")
    if rec and rec.get("back_diff") and filled(keys.get("NO-RETURN", "")) and \
            re.match(r"^(none|n/?a|nothing|no\b)", keys["NO-RETURN"], re.IGNORECASE):
        problems[3].append(f"{PLAN}: NO-RETURN says none, but the rehearsed way back does not give the data back")
    if rec and rec.get("back") and filled(keys.get("ROLLBACK", "")):
        verb = rec["back"].split()[-2:] if len(rec["back"].split()) > 1 else rec["back"].split()
        if not any(w in keys["ROLLBACK"] for w in verb if len(w) > 1):
            problems[3].append(f"{PLAN}: ROLLBACK does not include the rehearsed way back `{rec['back']}`")
    for c in (carried or []):
        if not filled(carries.get(c, "")):
            problems[3].append(f"{PLAN}: the release carries {c}; say what it changes in production")
    for c in carries:
        if carried is not None and c not in carried:
            problems[3].append(f"{PLAN}: CARRIES {c}, which is not changed; delete the line")
    live = ledger.get("live", {})
    for d, h in live.items():
        p = os.path.join(repo, d)
        if not os.path.exists(p) or sha(p) != h:
            problems[3].append(f"the live data {d} is not as it was when the work started. Nothing here may write "
                               "to it: rehearse on copies, and leave running the release to its owner")

    # A hold is a finished answer when the rehearsal is this tree's: what keeps stages 1-2 open is its reason.
    current = bool(rec) and rec.get("tree") == product_files(repo, rec["data"])
    holding = call == "hold" and current and not problems[3] and (problems[1] or problems[2])
    names = {1: "forward: rehearsed on a copy of the live data", 2: "back: today's code and the data survive the way back",
             3: "call: the plan is filled and the live data untouched"}
    for g in (1, 2, 3):
        state = "holds" if not problems[g] else (f"open, {len(problems[g])} blocker(s) the hold reports" if holding
                                                 else f"open, {len(problems[g])} to fix")
        print(f"STAGE {g} {names[g]}: {state}")
        for line in problems[g]:
            print(f"  - {line}")
    open_stages = [g for g in (1, 2, 3) if problems[g]]
    if open_stages and not holding:
        print(f"RELEASE-GATE: open({', '.join(map(str, open_stages))}): fix the lines above, then R --gate"
              + ("" if call == "hold" or not problems[1] + problems[2] else
                 ", or, if these are why it cannot go out, make the call hold"))
        return 1
    answer(rec, keys, named, carried or [], problems[1] + problems[2] if holding else [])
    return 0


def answer(rec, keys, named, carried, blockers=()):
    print("\nANSWER (drafted from the rehearsal and the plan; give it, adding only context):\n")
    print(f"Call: {keys['CALL']}")
    if blockers:
        print("Why it holds, as rehearsed on a copy of the live data:")
        for b in blockers:
            print(f"- {b.split('. ')[0][:300]}")
        print(f"\nRELEASE-GATE: done(hold, {len(blockers)} blocker{'s' if len(blockers) != 1 else ''})")
        return
    print(f"Rollback: {keys['ROLLBACK']}")
    print(f"Point of no return: {keys['NO-RETURN']}")
    print(f"Watch: {keys['WATCH']}")
    print(f"\nRehearsed on copies of {', '.join(rec['data'])} (the live data was not touched), with today's code "
          f"from {rec.get('old')}:")
    print(f"- forward `{rec['forward']}`: " + "; ".join(rec.get("forward_changes", [])[:4]) + "; safe to run twice")
    print(f"- the changed code's probes pass on the migrated data; today's code "
          + ("passes on it too (deploy window and a code-only revert are safe)" if not any(
              r["exit"] != 0 for r in rec.get("probes_window") or []) else f"fails on it; window: {keys.get('WINDOW')}"))
    print(f"- back `{rec['back']}`: " + ("gives every row back" if not rec.get("back_diff") else
                                          "loses: " + "; ".join(rec["back_diff"][:4])))
    for kind, word in (("DROPS", "drops"), ("LOSES", "loses")):
        for entry in named.get(kind, []):
            print(f"- {word} {entry}")
    print(f"- probes: {'; '.join('`' + p + '`' for p in rec['probes'])}")
    print(f"Carries: {', '.join(carried) if carried else 'no file changes'}.")
    print("Not covered: [[fill: what no rehearsal here reaches: the real deploy, traffic, other services, "
          "config and secrets on the server]]")
    print(f"\nRELEASE-GATE: done({first_word(keys['CALL'])}, "
          f"{'lossless' if not rec.get('back_diff') else 'lossy'} way back)")


def overview(repo):
    ledger = load(repo)
    data = find_data(repo, ledger.get("data_named") or [])
    if data and not pick_old(repo, ledger, None, data):
        first_touch(repo, ledger, data)
        save(repo, ledger)
    print(f"live data: {', '.join(data) if data else 'none found (name it with --data PATH)'}")
    if ledger.get("old"):
        o = ledger["old"]
        print(f"today's code: {'git ' + o['ref'] if o['kind'] == 'git' else o['path']}")
    if ledger.get("old_note"):
        print(f"  ({ledger['old_note']}; pass --old REF|DIR if production runs something else)")
    rec = ledger.get("rehearsal")
    if rec:
        show_rehearsal(rec)
    print('next: R --rehearse --forward "<cmd>" --back "<cmd>" --probe "<cmd>", then R --gate')
    return 0


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description="Rehearse a release and its way back on copies of the live data.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--rehearse", action="store_true", help="run the rehearsal")
    ap.add_argument("--forward", metavar="CMD", help="the step that applies the change to the data")
    ap.add_argument("--back", metavar="CMD", help="the step that undoes it")
    ap.add_argument("--probe", action="append", metavar="CMD", help="a command that uses the data through the code")
    ap.add_argument("--old", metavar="REF|DIR", help="the code that runs today (default: git HEAD, else the tree "
                                                     "at the first call)")
    ap.add_argument("--data", action="append", metavar="PATH", help="a live data file the scan misses")
    ap.add_argument("--gate", action="store_true", help="check the three stages")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per command")
    a = ap.parse_args(argv)
    repo = os.path.abspath(a.repo)
    if a.rehearse:
        return rehearse(repo, a.forward, a.back, a.probe or [], a.old, a.data or [], a.timeout)
    if a.gate:
        return gate(repo)
    if a.old or a.data:
        ledger = load(repo)
        data = find_data(repo, a.data or [])
        ledger["data_named"] = sorted(set((ledger.get("data_named") or []) + (a.data or [])))
        err = pick_old(repo, ledger, a.old, data)
        if err:
            print(err)
            return 2
        first_touch(repo, ledger, data)
        save(repo, ledger)
    return overview(repo)


if __name__ == "__main__":
    sys.exit(main())
