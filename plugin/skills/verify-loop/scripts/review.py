"""review.py — review a change by proof: `verify.py review [repo] [--base REF]`.

A review here is a list of findings a person can re-run, not opinions. Two kinds:

  high    the change weakened its own proof: a test removed, skipped, hollowed or with fewer
          assertions; a check, fail-signal, requirement or feature dropped from VERIFY.md; an
          oracle or check script edited alongside the code it judges.
  medium  the change is not proven: a changed line no check reaches (UNCOVERED), a mutant of a
          changed line that every check lets through (SURVIVED), a changed product file no
          feature maps (UNMAPPED), or no mutation survey possible (NOT SURVEYED).

It reads and never writes: no state, no receipts, no edits. Mutations run in scratch copies through
the same survey as `swarm --auto --diff`.
"""
import json
import os
import subprocess

from mutate import detect_lang, git_lines
from swarm import Unsurveyable, survey


def _git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True)


def resolve(repo, base):
    """The commit SHA of `base`; ValueError when `repo` is not a git work tree or `base` is not a commit."""
    p = _git(repo, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
    if p.returncode:
        raise ValueError(f"{base!r} is not a commit in {repo}")
    return p.stdout.decode().strip()


def at_base(repo, sha, rel):
    """File content at the base commit, or None when it did not exist there."""
    p = _git(repo, "show", f"{sha}:{rel}")
    return None if p.returncode else p.stdout.decode("utf-8", errors="replace")


def current(repo, rel):
    path = os.path.join(repo, rel)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def changes(v, repo, sha):
    """[(old path or None, new path or None)] for every file changed since `sha`, untracked included.
    Renames pair their two names so a moved test file is compared, not reported as removed."""
    out = []
    for line in git_lines(repo, "diff", "--name-status", "-M", "--relative", sha):
        parts = line.split("\t")
        status = parts[0][:1]
        if status == "R":
            out.append((parts[1], parts[2]))
        elif status == "D":
            out.append((parts[1], None))
        elif status == "A":
            out.append((None, parts[1]))
        else:
            out.append((parts[1], parts[1]))
    out += [(None, rel) for rel in git_lines(repo, "ls-files", "--others", "--exclude-standard")]
    return [(o, n) for o, n in out
            if not any(v.is_state_file(part) for part in (n or o).split("/"))]


def is_test(v, rel):
    base = (rel or "").rsplit("/", 1)[-1]
    return bool(v.TEST_PY.match(base) or v.TEST_JS.match(base) or v.TEST_GO.match(base))


def finding(kind, file, detail, line=None, reproduce=""):
    high = kind.startswith(("TEST", "CHECK", "SIGNAL", "ORACLE", "FEATURE", "REQUIREMENT"))
    return {"kind": kind, "severity": "high" if high else "medium", "file": file, "line": line,
            "detail": detail, "reproduce": reproduce}


def test_findings(v, repo, sha, pairs):
    out = []
    for old, new in pairs:
        if not old or not is_test(v, old):
            continue
        old_text = at_base(repo, sha, old)
        if old_text is None:
            continue
        before = v.tests_in_text(old_text, old)
        after = v.tests_in_text(current(repo, new), new) if new and current(repo, new) is not None else []
        if before is None:
            continue
        where = new or old
        if after is None:
            out.append(finding("TEST UNREADABLE", where, "parsed at the base, does not parse now"))
            continue
        now = {name: (flag, skip, count) for name, flag, skip, count in after}
        for name, flag, skip, count in before:
            if name not in now:
                gone = "the file was deleted" if new is None else "it is gone"
                out.append(finding("TEST REMOVED", where, f"{name} was in the base and {gone}"))
                continue
            n_flag, n_skip, n_count = now[name]
            if n_skip and not skip:
                out.append(finding("TEST SKIPPED", where, f"{name} now skipped"))
            if n_count < count:
                out.append(finding("TEST WEAKENED", where, f"{name}: {count} -> {n_count} assertions"))
            elif n_flag and not flag:
                out.append(finding("TEST HOLLOWED", where, f"{name}: {n_flag}"))
    return out


def check_findings(v, repo, sha, pairs):
    old_text = at_base(repo, sha, v.RECIPE)
    if old_text is None:
        return []
    new_text = current(repo, v.RECIPE) or ""
    old_f, _ = v.parse(old_text)
    new_f, _ = v.parse(new_text, repo=repo)
    now = {f["name"]: f for f in new_f}
    out = []
    for f in old_f:
        g = now.get(f["name"])
        if g is None:
            out.append(finding("FEATURE REMOVED", v.RECIPE, f"## {f['name']} and its {len(f['checks'])} check(s)"))
            continue
        for kind, cmd in f["checks"]:
            if (kind, cmd) not in g["checks"]:
                out.append(finding("CHECK REMOVED", v.RECIPE, f"{f['name']}: {kind}: `{cmd}` removed or edited"))
        if f["signals"] != g["signals"]:
            out.append(finding("SIGNAL CHANGED", v.RECIPE,
                               f"{f['name']}: fail-signal {f['signals']} -> {g['signals']}"))
    for word in v.requirements(old_text):
        if word not in v.requirements(new_text):
            out.append(finding("REQUIREMENT REMOVED", v.RECIPE, f"require: {word}"))

    oracles = {o.replace("\\", "/") for f in old_f for o in f["oracles"]}
    try:
        frozen = set(v.check_hashes(repo))
    except (OSError, ValueError):
        frozen = set()
    scripts = {k for k in frozen if os.path.isfile(os.path.join(repo, k))} - oracles
    for old, new in pairs:
        if old in oracles:
            what = "deleted" if new is None else "edited"
            out.append(finding("ORACLE CHANGED", old, f"expected data {what} in the same change as the code it judges"))
        elif old in scripts and not is_test(v, old) and old != v.RECIPE:
            out.append(finding("CHECK CHANGED", old, "check script edited in the same change as the code it judges"))
    return out


RANK = {"inconclusive": 0, "uncovered": 1, "survived": 2, "caught": 3}


def mutation_findings(v, repo, sha, base, jobs, limit, timeout):
    """(findings, summary). Survivors and unreached changed lines, one finding per line."""
    try:
        s = survey(v, repo, diff=sha, jobs=jobs, limit=limit, timeout=timeout)
    except Unsurveyable as exc:
        verdict, reason = exc.args
        if reason.startswith(("no changed product file", "no mutable lines")):
            return [], {"skipped": reason}
        return [finding("NOT SURVEYED", v.RECIPE, f"mutation survey {verdict}: {reason}")], {"skipped": reason}
    # The survey judges each mutant once per feature; a review asks whether ANY check catches it.
    merged = {}
    for r in s["results"]:
        key = (r["file"], r["line"], r["before"], r["after"])
        rank = RANK.get(r["verdict"], 0)
        if key not in merged or rank > RANK.get(merged[key]["verdict"], 0):
            merged[key] = r
    results = list(merged.values())
    script = os.path.abspath(v.__file__)
    out, seen = [], set()
    for r in results:
        kind = {"survived": "SURVIVED", "uncovered": "UNCOVERED"}.get(r["verdict"])
        if not kind or (kind, r["file"], r["line"]) in seen:
            continue
        seen.add((kind, r["file"], r["line"]))
        detail = (f"[{r['feature']}] {r['operator']}: `{r['before'].strip()}` -> `{r['after'].strip()}` passes every check"
                  if kind == "SURVIVED" else
                  f"[{r['feature']}] no check reaches `{r['before'].strip()}`")
        cmd = (f"python {json.dumps(script)} challenge {json.dumps(repo)} --feature {json.dumps(r['feature'])} "
               f"--file {json.dumps(r['file'])} --before {json.dumps(r['before'])} --after {json.dumps(r['after'])}")
        out.append(finding(kind, r["file"], detail, line=r["line"], reproduce=cmd))
    count = {k: sum(r["verdict"] == k for r in results) for k in ("caught", "survived", "uncovered")}
    decided = sum(count.values())
    return out, dict(count, inconclusive=len(results) - decided, mutants=len(results),
                     score=round(count["caught"] / decided, 3) if decided else None,
                     files=s["files"], features=s["features"])


def cmd_review(v, repo, base="HEAD", mutate=True, jobs=1, limit=20, timeout=120, as_json=False):
    try:
        sha = resolve(repo, base)
        pairs = changes(v, repo, sha)
    except ValueError as exc:
        print(f"REVIEW: cannot review ({exc})")
        return 2
    findings = test_findings(v, repo, sha, pairs) + check_findings(v, repo, sha, pairs)

    has_recipe = os.path.isfile(os.path.join(repo, v.RECIPE))
    product = sorted(n for _, n in pairs if n and detect_lang(n) != "other" and not is_test(v, n))
    try:
        frozen = set(v.check_hashes(repo)) if has_recipe else set()
    except (OSError, ValueError):
        frozen = set()
    product = [p for p in product if p not in frozen]
    if not product:
        mutation = {"skipped": "no changed product file"}
    elif not has_recipe:
        mutation = {"skipped": f"no {v.RECIPE}"}
        findings.append(finding("NOT SURVEYED", v.RECIPE,
                                f"no {v.RECIPE}: no check judges the {len(product)} changed product file(s)"))
    elif not mutate:
        mutation = {"skipped": "--no-mutate"}
    else:
        more, mutation = mutation_findings(v, repo, sha, base, jobs, limit, timeout)
        findings += more

    surveyed = {r for r in mutation.get("files", [])} if "files" in mutation else set()
    features = v.parse(v.read(repo, v.RECIPE), repo=repo)[0] if has_recipe else []
    for rel in product if has_recipe else []:
        if rel in surveyed:
            continue  # its lines were judged one by one
        if not any(v.is_feature_affected(f, {rel}, repo) for f in features):
            findings.append(finding("UNMAPPED", rel, "changed product file that no feature in VERIFY.md names"))

    findings.sort(key=lambda f: (f["severity"] != "high", f["kind"], f["file"], f["line"] or 0))
    state, detail, _ = v.status_verdict(repo)
    code = 1 if findings else 0
    if as_json:
        print(json.dumps({"base": base, "base_sha": sha, "findings": findings, "mutation": mutation,
                          "state": {"verdict": state, "detail": detail}, "exit": code}, indent=2))
        return code
    since = f"since {base} ({sha[:7]})"
    print(f"REVIEW: {len(findings)} finding(s) in the change {since}" if findings
          else f"REVIEW: clean, no finding in the change {since}")
    for f in findings:
        where = f["file"] + (f":{f['line']}" if f["line"] else "")
        print(f"  {f['severity'].upper()}  {f['kind']}  {where}  {f['detail']}")
        if f["reproduce"]:
            print(f"      reproduce: {f['reproduce']}")
    if "skipped" in mutation:
        print(f"MUTATION: not run ({mutation['skipped']})")
    else:
        decided = mutation["caught"] + mutation["survived"] + mutation["uncovered"]
        shown = "n/a" if mutation["score"] is None else f"{mutation['score']:.0%}"
        print(f"MUTATION: {mutation['caught']}/{decided} caught on changed lines (score {shown}), "
              f"{mutation['uncovered']} uncovered, {mutation['inconclusive']} inconclusive")
    print(f"VERIFY-STATE: {state}" + (f" ({detail})" if detail else ""))
    return code
