#!/usr/bin/env python3
"""
cadence-check — mechanical enforcement of PROTOCOL §12 (run-cadence obligation).

§12 requires one live run against a real external subject (a `runs/LIVE_RUN_*.md`
file) per release that changes a skill *body* — and shipped, in v1.20.1,
as pure prose with no gate watching it, which is the identical "repayment
triggers are prose nobody watches" failure IMPROVEMENT_PLAN.md's F4 named and
LIVE_RUN_005 then independently confirmed on a second codebase. This tool is
that gate: for every CHANGELOG.md release from CADENCE_INTRODUCED_AT onward
(rule-vintage, PROTOCOL §11 — a rule may not condemn a release before it
existed), it checks whether the release's commit changed any skill body and,
if so, whether a `runs/LIVE_RUN_*.md` file was added in the same commit — with
no minor/patch distinction, per §12 / DECISION_LEDGER.md D007: a skill-body
change is never patch-level in its own right.

"Skill body" excludes YAML frontmatter (the F1 trigger-text budget doctrine-
budget.py already tracks) — only the contract text below the frontmatter
counts, matching §12's own wording ("changes a skill body (not frontmatter,
tools, or docs)").

Release -> commit mapping relies on this repo's own convention: a release's
commit subject starts with "<version>: " or "v<version>: " (verified against
git log across 1.14.0-1.20.0 before writing this). A version CHANGELOG.md
declares with no matching commit is reported as unmappable, not silently
skipped — the same "never silently skip a stage" discipline as run-trace.py.

Exit codes: 0 clean, 1 gap(s) found, 2 could not measure.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

from _encoding import utf8_streams

CADENCE_INTRODUCED_AT = (1, 20, 1)
VERSION_RE = re.compile(r"^## (\d+)\.(\d+)\.(\d+)\b")
LIVE_RUN_RE = re.compile(r"^runs/LIVE_RUN_\d+\.md$")


class CadenceBlocked(Exception):
    """Raised when the cadence surface cannot be measured."""


def parse_changelog_versions(text: str) -> list[tuple[int, int, int]]:
    """Ordered newest-first list of (major, minor, patch) release headers."""
    out = []
    for line in text.splitlines():
        m = VERSION_RE.match(line)
        if m:
            out.append(tuple(int(g) for g in m.groups()))
    return out


def evaluate(releases: list[dict], introduced_at=CADENCE_INTRODUCED_AT) -> list[dict]:
    """Pure logic, no git/IO: `releases` is newest-first, each a dict with
    keys version (tuple), body_changed (bool|None — None = unmappable),
    live_run_added (bool). Returns the gap rows (version, reason)."""
    gaps = []
    for r in releases:
        if r["version"] < introduced_at:
            continue  # rule-vintage: §12 does not condemn history before it existed
        if r["body_changed"] is None:
            gaps.append({"version": r["version"], "reason": "unmappable(no commit found)"})
        elif r["body_changed"] and not r["live_run_added"]:
            gaps.append({"version": r["version"], "reason": "skill-body-changing, no LIVE_RUN added"})
    return gaps


def _git(root: Path, *args: str) -> str:
    res = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if res.returncode != 0:
        raise CadenceBlocked(f"git {' '.join(args)} failed: {res.stderr.strip()}")
    return res.stdout


def _find_commit(root: Path, version: tuple[int, int, int]) -> str | None:
    v = ".".join(str(n) for n in version)
    log = _git(root, "log", "--all", "--format=%H\t%s")
    for line in log.splitlines():
        sha, _, subject = line.partition("\t")
        subject = subject.strip()
        if subject.startswith(f"{v}:") or subject.startswith(f"v{v}:"):
            return sha
    return None


def _body_changed(root: Path, commit: str) -> bool:
    """True if `commit` touches any skills/*/SKILL.md line outside frontmatter."""
    changed = _git(root, "show", "--name-only", "--format=", commit).splitlines()
    skill_files = [f for f in changed if re.match(r"^skills/[^/]+/SKILL\.md$", f)]
    for f in skill_files:
        try:
            after = _git(root, "show", f"{commit}:{f}")
        except CadenceBlocked:
            continue  # file deleted in this commit — not a body-content change to check
        fm = re.match(r"^---\n.*?\n---\n", after, re.S)
        body_start_line = after[:fm.end()].count("\n") + 1 if fm else 1
        diff = _git(root, "diff", f"{commit}^", commit, "--", f)
        # unified diff hunk headers give the touched line range in the new file
        for hunk in re.finditer(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", diff, re.M):
            new_start = int(hunk.group(3))
            new_len = int(hunk.group(4) or 1)
            if new_start + new_len > body_start_line:
                return True
    return False


def _live_run_added(root: Path, commit: str) -> bool:
    changed = _git(root, "show", "--name-status", "--format=", commit).splitlines()
    for line in changed:
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].startswith("A") and LIVE_RUN_RE.match(parts[-1]):
            return True
    return False


def measure(root: Path) -> list[dict]:
    changelog = root / "CHANGELOG.md"
    if not changelog.is_file():
        raise CadenceBlocked(f"{changelog}: not found")
    versions = parse_changelog_versions(changelog.read_text(encoding="utf-8"))
    if not versions:
        raise CadenceBlocked(f"{changelog}: no '## X.Y.Z' release headers found")

    releases = []
    for version in versions:
        if version < CADENCE_INTRODUCED_AT:
            releases.append({"version": version, "body_changed": None, "live_run_added": False})
            continue
        commit = _find_commit(root, version)
        if commit is None:
            releases.append({"version": version, "body_changed": None, "live_run_added": False})
            continue
        releases.append({
            "version": version,
            "body_changed": _body_changed(root, commit),
            "live_run_added": _live_run_added(root, commit),
        })
    return releases


def die(code: int, msg: str) -> None:
    print(f"cadence-check: {msg}", file=sys.stderr)
    print(f"CADENCE: blocked({msg})")
    raise SystemExit(code)


def main() -> int:
    utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".", type=Path, help="suite root (has CHANGELOG.md and .git)")
    args = ap.parse_args()

    try:
        releases = measure(args.root)
    except CadenceBlocked as e:
        die(2, str(e))

    gaps = evaluate(releases)
    checked = [r for r in releases if r["version"] >= CADENCE_INTRODUCED_AT]

    if gaps:
        print(f"cadence-check: {len(gaps)} gap(s) since "
              f"{'.'.join(str(n) for n in CADENCE_INTRODUCED_AT)}:")
        for g in gaps:
            v = ".".join(str(n) for n in g["version"])
            print(f"  · {v} — {g['reason']}")
        print(f"CADENCE: gap({len(gaps)})")
        return 1

    print(f"cadence-check: {len(checked)} release(s) checked since "
          f"{'.'.join(str(n) for n in CADENCE_INTRODUCED_AT)}, no gap")
    print(f"CADENCE: clean({len(checked)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
