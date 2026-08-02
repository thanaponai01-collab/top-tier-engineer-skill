#!/usr/bin/env python3
"""
doctrine-budget — measure the suite's own context tax (IMPROVEMENT_PLAN.md B4).

PROTOCOL.md is monotonic — every earned rule is permanent, each release adds
more — and nothing watched the total. This is that watcher, using the same
ratchet the suite already applies to code: freeze a byte count, name a
`repay_at`, fail loud when crossed. It measures bytes-loaded-per-session: the
full text of PROTOCOL.md (loaded once per session, PROTOCOL §0), every skill's
YAML frontmatter (loaded whenever the harness lists skills — this is the F1
budget), and chief-engineer's full body (read entire at Phase 0, per its own
wiring note).

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
    frontmatter_total = 0
    skill_files = sorted((root / "skills").glob("*/SKILL.md"))
    if not skill_files:
        raise DoctrineBlocked(f"{root / 'skills'}: no SKILL.md files found")
    for f in skill_files:
        if f == chief:
            continue  # already counted whole above; avoid double-counting its frontmatter
        frontmatter_total += frontmatter_bytes(f)
    parts["skill frontmatter (18 others)"] = frontmatter_total

    return {"parts": parts, "total": sum(parts.values()), "skill_count": len(skill_files)}


def die(code: int, msg: str) -> None:
    print(f"doctrine-budget: {msg}", file=sys.stderr)
    print(f"DOCTRINE: blocked({msg})")
    raise SystemExit(code)


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
        repay_at = None
        if args.write_baseline.is_file():
            try:
                repay_at = json.loads(args.write_baseline.read_text(encoding="utf-8")).get("repay_at")
            except (json.JSONDecodeError, OSError):
                pass
        payload = {"bytes": m["total"]}
        if repay_at is not None:
            payload["repay_at"] = repay_at
        args.write_baseline.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    repay_at = None
    if args.baseline:
        if not args.baseline.is_file():
            die(2, f"{args.baseline}: not found — pass --write-baseline once to create it")
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        repay_at = baseline.get("repay_at")

    exit_code = 0
    if repay_at is not None and m["total"] >= repay_at:
        state = f"budget-exceeded({m['total']}/{repay_at})"
        exit_code = 1
    elif repay_at is not None:
        state = f"clean(bytes: {m['total']}, headroom: {repay_at - m['total']})"
    else:
        state = f"clean(bytes: {m['total']})"

    if args.json:
        print(json.dumps({**m, "repay_at": repay_at, "verdict": state}, indent=2))
    else:
        print(f"doctrine-budget: {m['skill_count']} skills, {m['total']} bytes total")
        for name, n in m["parts"].items():
            print(f"  {name}: {n}")
        if repay_at is not None:
            print(f"  repay_at: {repay_at}")

    print(f"DOCTRINE: {state}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
