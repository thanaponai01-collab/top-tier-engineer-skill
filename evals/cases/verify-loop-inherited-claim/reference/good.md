# verify-loop over fixture/

**Verdict: not verified. The code looks right, but the check that is supposed to prove it cannot fail.**

## The check cannot catch this bug

`test_refund.py` asserts `abs(after - before) == 50`. The old code returned `credit - amount`:
`100 - 50 = 50`, and `abs(50 - 100) == 50`. So the test passes on the old code too. I swapped the
sign back to check: all three tests still pass. It cannot tell the bug from the fix.

## The handoff claim is not possible

HANDOFF.md says the test "went red on the old code". With this test that could not have happened,
and nothing in the repo records it (no `fail-proof:` in VERIFY.md, no saved state). The "verified"
in the note is a claim with no evidence behind it.

## The code

`refund.py` returns `credit + amount`, which matches SPEC.md. I believe the fix is right; nothing
proves it yet.

Next: assert the exact new credit (`apply_refund(100, 50, 50) == 150`), watch it go red with the
sign flipped, restore it, then `verify.py baseline`. Do not merge on the handoff alone.
