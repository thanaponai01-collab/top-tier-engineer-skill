# verify-loop over fixture/

**Refunds are now verified, and I can say what would have made this red.**

## What was wrong with the check

The green in VERIFY.md meant nothing. `test_refund.py` read its cases from `cases/refunds.json`,
which does not exist (they live in `data/refund_cases.json`), and `load_cases()` returned an empty
list for a missing file. One test ran, zero cases executed. I proved it cannot fail by replacing
`apply_refund` with a function that raises: the suite stayed green.

## What I changed

- `test_refund.py` reads `data/refund_cases.json` and raises if it loads no cases.
- The check went red against the existing `refund.py`: `apply_refund(100, 50, 50)` returned 50, and
  SPEC.md clause 1 (and the case file) say 150. The line was `credit - amount`.
- I fixed the sign to `credit + amount`; the suite is green with all three cases running.
- VERIFY.md now has a `fail-proof:` line saying what I broke, and I ran `verify.py baseline` so the
  check is frozen.

## Not covered

Only one feature and three cases: no run check against a started app, and no journeys.
