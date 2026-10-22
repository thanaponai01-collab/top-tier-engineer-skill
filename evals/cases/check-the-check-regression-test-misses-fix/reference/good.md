# PR #13 review: the regression test does not prove the fix

**Verdict: no. The code change fixes #12, but `test_due_date_is_not_late` would have passed before
the fix too, so it proves nothing about it.**

## What I ran

I checked out `main`'s `billing.py` in a scratch copy and ran the PR's test file against it:
`test_due_date_is_not_late` passes on main. Back on the PR branch it passes too. A regression test
that is green on the buggy code can't catch the bug.

## Why

The bug was in `invoice_total`: on main it worked out the fee itself with `paid >= due`, so a
payment on the due date was charged. `late_fee` was already correct (`paid > due`) and the PR did
not change it. The PR routes `invoice_total` through `late_fee`, which is the real fix, but the new
test calls `late_fee` only.

## What would prove it

Add `invoice_total(200.0, DUE, DUE) == 200.0`. On main it returns 210.0 and fails; on the PR it
passes. With that test the PR is ready.
