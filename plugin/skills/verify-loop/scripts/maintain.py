"""Maintain mode: a read-only audit of a project verify skill against VERIFY.md, proof and churn.

It runs nothing and edits nothing. It says, per mapped feature, what the next pass must do:

  map        VERIFY.md feature with no feature file in .claude/skills/verify/features/
  re-prove   no current rejection receipt matching its fail-signal (checks changed, or never red)
  fix        its last recorded check failed: triage it (harness gap, map drift or product gap)
  re-drive   source it names changed since the last maintained commit
  drive      nothing flagged; the live pass still drives it once

plus the skill's shape problems (skill-check), checks changed since the baseline, and changed
files no feature claims. The last maintained commit is the `last-maintained: <sha>` line in
features/README.md, which survives fresh clones; `--since REF` overrides it.
"""
import json
import os
import re
import subprocess

from create import SKILL_DIR, _read, skill_problems

ACTIONS = ("map", "re-prove", "fix", "re-drive", "drive")
IGNORED = (".verify-", "__pycache__/", ".git/")


def last_maintained(repo):
    m = re.search(r"(?m)^last-maintained:\s*([0-9a-fA-F]{7,40})\s*$",
                  _read(os.path.join(repo, SKILL_DIR, "features", "README.md")))
    return m.group(1) if m else None


def changed_since(repo, ref):
    """Repo-relative files changed since ref (committed, staged, unstaged, untracked); None if no git."""
    def git(*args):
        p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if p.returncode:
            raise ValueError(p.stderr.strip() or f"git {' '.join(args)} failed")
        return {ln.strip().replace("\\", "/") for ln in p.stdout.splitlines() if ln.strip()}

    try:
        files = git("diff", "--name-only", "--relative", ref or "HEAD")
        files |= git("ls-files", "--others", "--exclude-standard")
    except (OSError, ValueError):
        return None
    return sorted(f for f in files if not any(f.startswith(i) or ("/" + i) in f for i in IGNORED))


def audit(v, repo, since=None):
    base = os.path.join(repo, SKILL_DIR)
    if not os.path.isfile(os.path.join(base, "SKILL.md")):
        return {"outcome": "blocked", "detail": f"no {SKILL_DIR}/SKILL.md: use create mode first",
                "exit": 2}
    shape = skill_problems(v, repo)
    features = []
    if os.path.isfile(os.path.join(repo, v.RECIPE)):
        features = [f for f in v.parse(v.read(repo, v.RECIPE), repo=repo)[0] if not f["journey"]]
    fdir = os.path.join(base, "features")
    mapped = {}
    for name in sorted(os.listdir(fdir)) if os.path.isdir(fdir) else []:
        m = re.search(r"(?m)^verify-section:\s*(.+?)\s*$", _read(os.path.join(fdir, name)))
        if name.endswith(".md") and name != "README.md" and m:
            mapped.setdefault(m.group(1), []).append(f"features/{name}")

    state = v.load_state(repo)
    try:
        hashes = v.check_hashes(repo)
        signature = v.sha(json.dumps(hashes, sort_keys=True))
        baseline_drift = v.tampered(repo, state)
    except (OSError, ValueError) as exc:
        hashes, signature, baseline_drift = {}, None, [str(exc)]
    frozen = {k for k, h in (state.get("baseline") or {}).items() if hashes.get(k) == h}
    receipts = v.current_receipts(state, signature) if signature else {}
    checks = state.get("checks", {}) or {}

    ref = since or last_maintained(repo)
    changed = changed_since(repo, ref)
    if changed is not None:
        # A check input that matches the baseline was reviewed and frozen after it changed.
        changed = [c for c in changed if c not in frozen]
    rows, claimed = [], set()
    for f in features:
        hits = [c for c in (changed or []) if v.is_feature_affected(f, {c}, repo)]
        claimed.update(hits)
        last = [checks.get(f"{f['name']}|{cmd}", {}) for _, cmd in f["checks"]]
        run = ("never" if not f["checks"] or not all(last) else
               "fail" if any(not r.get("ok") for r in last) else "pass")
        proven = bool(f["proofs"]) and bool(signature) and v.proven_by(f, receipts, signature) is not None
        action = ("map" if f["name"] not in mapped else
                  "re-prove" if not proven else
                  "fix" if run == "fail" else
                  "re-drive" if hits else "drive")
        rows.append({"feature": f["name"], "map": mapped.get(f["name"], []), "last_run": run,
                     "proven": proven, "changed": hits, "action": action})
    skill_rel = SKILL_DIR.replace(os.sep, "/") + "/"
    own = {v.RECIPE, "README.md", "CHANGELOG.md", ".gitignore"}
    unclaimed = [c for c in (changed or []) if c not in claimed and c not in own
                 and not c.startswith(skill_rel) and not c.endswith(".md")]
    attention = [r for r in rows if r["action"] != "drive"]
    return {
        "outcome": "audit", "since": ref, "git": changed is not None,
        "features": rows, "shape": shape, "baseline_drift": baseline_drift,
        "unclaimed_changes": unclaimed, "verdict": v.answer(repo)["verdict"],
        "attention": len(attention) + len(shape) + len(baseline_drift) + len(unclaimed),
        "exit": 1 if attention or shape or baseline_drift or unclaimed else 0,
    }


def cmd_maintain(v, repo, since=None, as_json=False):
    a = audit(v, repo, since)
    if as_json:
        print(json.dumps(a, indent=2))
        return a["exit"]
    if a["outcome"] == "blocked":
        print(f"MAINTAIN: blocked ({a['detail']})")
        return a["exit"]
    if not a["git"]:
        print(f"note  no git history{' at ' + a['since'] if a['since'] else ''}: churn not checked")
    elif not a["since"]:
        print("note  no last-maintained line in features/README.md: churn is uncommitted changes only")
    for r in a["features"]:
        extra = f" changed: {', '.join(r['changed'][:3])}" if r["changed"] else ""
        print(f"  {r['action'].upper():9} {r['feature']}  [last run {r['last_run']}; "
              f"{'proven' if r['proven'] else 'never seen red'}]{extra}")
    for p in a["shape"]:
        print(f"  SHAPE     {p}")
    for c in a["baseline_drift"]:
        print(f"  BASELINE  {c} differs from the baseline: a person reviews it before `baseline`")
    for c in a["unclaimed_changes"]:
        print(f"  UNCLAIMED {c} changed and no feature names it: map it, or say why it is not user-facing")
    print(f"MAINTAIN: {len(a['features'])} feature(s), {a['attention']} need attention; "
          f"verdict {a['verdict']}. Every feature is still driven live once.")
    return a["exit"]
