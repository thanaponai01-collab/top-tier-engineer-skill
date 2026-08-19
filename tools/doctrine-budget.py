#!/usr/bin/env python3
"""
doctrine-budget — measure the suite's own context tax (IMPROVEMENT_PLAN.md B4).

PROTOCOL.md is monotonic — every earned rule is permanent, each release adds
more — and nothing watched the total. This is that watcher, using the same
ratchet the suite already applies to code: freeze a byte count, name a
`repay_at`, fail loud when crossed. It measures bytes-loaded-per-session: the
full text of PROTOCOL.md (loaded once per session, PROTOCOL §0), GATE_DOCTRINE.md
(loaded once per isolated §8.2 gate agent), every skill's YAML frontmatter
(loaded whenever the harness lists skills — this is the F1 budget), and
chief-engineer's full body (read entire at Phase 0, per its own wiring note).

HOT vs COLD, and why the split is not gaming the gate
-----------------------------------------------------
PROTOCOL.md's rationale lives in PROTOCOL_RATIONALE.md, which no run loads —
PROTOCOL.md §0 says so and every skill points at it that way. Moving prose there
therefore genuinely stops costing per-session bytes, which is exactly the kind of
change this budget exists to reward. But a budget that only counts what someone
declares cold is a budget anyone can satisfy by relabelling, so the COLD total is
measured and printed on every run alongside the charged HOT total. Growth cannot
hide there silently; it just does not fail the build.

The per-gate figure is reported for the same reason: §8.2 runs gates in parallel
isolated contexts, each paying its own doctrine, so the session's true doctrine
cost is HOT plus (gate path x number of gates spawned) — a multiplier the single
charged number does not show.

This is a doctrine-tier analogue of structure-report.py's ratchet, kept
separate and small rather than folded in: structure-report.py is itself on
DEBT_LEDGER (D-3, `repay_at`: 700) with 17 lines of headroom at time of
writing, and a growing byte-budget tool has no business being the straw that
breaks a file already this close to its own trigger.

Exit codes: 0 clean or under repay_at, 1 repay_at crossed, 2 could not measure.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from _encoding import utf8_streams


class DoctrineBlocked(Exception):
    """Raised when the doctrine surface cannot be measured; carries the reason
    for the caller to fold into a `DOCTRINE: blocked(...)` verdict line rather
    than exiting silently."""


def frontmatter_bytes(skill_md: Path) -> int:
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n.*?\n---\n", text, re.S)
    return len(m.group(0).encode("utf-8")) if m else 0


def measure(root: Path) -> dict:
    protocol = root / "PROTOCOL.md"
    chief = root / "skills" / "chief-engineer" / "SKILL.md"
    if not protocol.is_file():
        raise DoctrineBlocked(f"{protocol}: not found")
    if not chief.is_file():
        raise DoctrineBlocked(f"{chief}: not found")

    parts = {
        "PROTOCOL.md": len(protocol.read_bytes()),
        "chief-engineer/SKILL.md (full body)": len(chief.read_bytes()),
    }
    # Optional: absent in a checkout that predates the gate stub, and in consuming
    # repos that vendored only the skills. Absence is zero bytes, not an error.
    gate = root / "GATE_DOCTRINE.md"
    gate_bytes = len(gate.read_bytes()) if gate.is_file() else 0
    if gate_bytes:
        parts["GATE_DOCTRINE.md"] = gate_bytes

    frontmatter_total = 0
    skill_files = sorted((root / "skills").glob("*/SKILL.md"))
    if not skill_files:
        raise DoctrineBlocked(f"{root / 'skills'}: no SKILL.md files found")
    for f in skill_files:
        if f == chief:
            continue  # already counted whole above; avoid double-counting its frontmatter
        frontmatter_total += frontmatter_bytes(f)
    parts[f"skill frontmatter ({len(skill_files) - 1} others)"] = frontmatter_total

    # Cold: measured and shown, never charged. See the module docstring for why both
    # halves are reported rather than only the one that can fail the build.
    rationale = root / "PROTOCOL_RATIONALE.md"
    cold = {}
    if rationale.is_file():
        cold["PROTOCOL_RATIONALE.md"] = len(rationale.read_bytes())

    # What one isolated §8.2 gate pays in its own fresh context: the stub plus the
    # heaviest gate skill body it may be told to execute. Reported, not charged —
    # the charged total is per-session, and gates are per-change.
    gate_skills = [root / "skills" / n / "SKILL.md" for n in
                   ("correctness-gate", "structure-gate", "threat-model",
                    "senior-review", "scrutinize")]
    heaviest = max((len(f.read_bytes()) for f in gate_skills if f.is_file()), default=0)

    return {"parts": parts, "total": sum(parts.values()), "skill_count": len(skill_files),
            "cold": cold, "cold_total": sum(cold.values()),
            "gate_path": gate_bytes + heaviest}


def die(code: int, msg: str) -> None:
    print(f"doctrine-budget: {msg}", file=sys.stderr)
    print(f"DOCTRINE: blocked({msg})")
    raise SystemExit(code)


def print_human_report(m: dict, repay_at) -> None:
    """The director-readable half of the output.

    Extracted from `main()` rather than added to it: `main()` was at 55 lines and
    cyclomatic 15 when the hot/cold split needed four more print branches, and PROTOCOL
    §10 rule 4 (carrying capacity) says the smallest diff into a function already at its
    threshold is a withdrawal, not the cheap option. The suite's own structural gate
    flagged it on this very change; extracting first is what the rule asks for.
    """
    print(f"doctrine-budget: {m['skill_count']} skills, {m['total']} bytes charged (hot)")
    for name, n in m["parts"].items():
        print(f"  {name}: {n}")
    if repay_at is not None:
        print(f"  repay_at: {repay_at}")
    if m["cold"]:
        print(f"  cold, not charged (no run loads it): {m['cold_total']}")
        for name, n in m["cold"].items():
            print(f"    {name}: {n}")
    if m["gate_path"]:
        print(f"  per isolated §8.2 gate, in its own context: {m['gate_path']}")


def write_baseline(path: Path, total: int) -> None:
    """Freeze `total` at `path`, preserving any `repay_at` already recorded there."""
    repay_at = None
    if path.is_file():
        try:
            repay_at = json.loads(path.read_text(encoding="utf-8")).get("repay_at")
        except (json.JSONDecodeError, OSError):
            pass
    payload = {"bytes": total}
    if repay_at is not None:
        payload["repay_at"] = repay_at
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def verdict(total: int, repay_at) -> tuple[str, int]:
    """The §5 DOCTRINE state and this run's exit code."""
    if repay_at is None:
        return f"clean(bytes: {total})", 0
    if total >= repay_at:
        return f"budget-exceeded({total}/{repay_at})", 1
    return f"clean(bytes: {total}, headroom: {repay_at - total})", 0


def main() -> int:
    utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".", type=Path, help="suite root (has PROTOCOL.md and skills/)")
    ap.add_argument("--baseline", metavar="FILE", type=Path,
                     help="JSON file with {\"bytes\": N, \"repay_at\": M} to ratchet against")
    ap.add_argument("--write-baseline", metavar="FILE", type=Path,
                     help="write the measured total (preserving repay_at) to FILE")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    try:
        m = measure(args.root)
    except DoctrineBlocked as e:
        die(2, f"{e} — cannot measure the doctrine surface")

    if args.write_baseline:
        write_baseline(args.write_baseline, m["total"])

    repay_at = None
    if args.baseline:
        if not args.baseline.is_file():
            die(2, f"{args.baseline}: not found — pass --write-baseline once to create it")
        repay_at = json.loads(args.baseline.read_text(encoding="utf-8")).get("repay_at")

    state, exit_code = verdict(m["total"], repay_at)

    if args.json:
        print(json.dumps({**m, "repay_at": repay_at, "verdict": state}, indent=2))
    else:
        print_human_report(m, repay_at)

    print(f"DOCTRINE: {state}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
