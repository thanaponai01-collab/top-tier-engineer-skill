---
name: verify-loop
description: Build the check before the work, then loop on it until it passes, so an agent can tell for itself whether it succeeded. Use at the start of any task with no way to tell it worked, when "done" was claimed without a run, when the human is the only one checking, or to map every feature to the tests that prove it (VERIFY.md).
---

# Verify Loop

Build the check before the work, make it hard to fool, and loop until it passes.

## What makes a check good

1. **It can fail.** Break the feature on purpose, see red, revert. A check that has never failed proves nothing.
2. **It watches the real thing.** Run the program, hit the endpoint, or drive the UI. Reading code is not a check.
3. **It does not come from the work.** Write the check from the spec/claim, not from the implementation.
4. **Its failure is specific.** Pinpoints expected vs actual values.
5. **It is cheap to rerun.** One fast command.

## The 7-step loop

1. **Name the claim:** Define observable finish conditions (e.g., "POST /refund returns 200 and balance drops").
2. **Choose strongest check:** types/lint → unit tests → integration tests → real run (`run:`).
3. **Record in VERIFY.md:** Draft with `verify.py init`. If no driver exists, scaffold one with `verify.py scaffold-driver`. (See [VERIFY_FORMAT.md](VERIFY_FORMAT.md)).
4. **Prove it can fail (Fail-proof):** Break feature, watch check go red, revert, record under `fail-proof:`. Freeze with `verify.py baseline`.
5. **Work in slices:** Run `verify.py run` after each edit. Obey warnings:
   - `NEWLY RED`: Last change broke a working check.
   - `SAME FAILURE x2`: Stop and rethink approach.
   - `BUDGET`: 5 red runs in a row; pause and report.
6. **Expectations are frozen:** Changing what a check expects requires human review and re-baseline.
7. **Prove done:** Run `verify.py status` (must be `green`). Use `verify.py run --strict` for releases.

## Fixing without disturbing (Scope Guard)

Prevent unintended collateral edits when fixing bugs:
1. `verify.py run` to confirm baseline state.
2. `verify.py scope <files>` to lock files the fix may touch.
3. Fix code in slices. `OUT OF SCOPE` warns if an unlisted file was edited; `KEEP-GREEN BROKEN` warns if a passing check broke.
4. `verify.py scope --clear` when complete.

## Failure Triage & Observable Evidence

- **Triage before fixing:** On failure, categorize into **Harness Gap**, **Doc Drift**, or **Product Gap** before modifying code. (See [TRIAGE.md](TRIAGE.md)).
- **Observable Evidence:** Save tangible runtime outputs (DOM snapshots, API payloads, screenshots) into `.verify-evidence/`.
- **Compliance checks:** Use `scripts/compliance.py` for schema, privacy, guardrail, and repeat checks. (See [COMPLIANCE.md](COMPLIANCE.md)).

## Quick command reference

```bash
python scripts/verify.py init              # Draft VERIFY.md from disk
python scripts/verify.py scaffold-driver   # Create runtime smoke driver & .verify-evidence/
python scripts/verify.py run [--strict]    # Run all checks (--strict enforces proofs)
python scripts/verify.py baseline          # Freeze check definitions
python scripts/verify.py scope <files>     # Restrict allowed edit paths
python scripts/verify.py status            # Check if last run is green and up-to-date
```
