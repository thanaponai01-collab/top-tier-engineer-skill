**No, the regression test does not prove the bug is fixed.** It passes on `main`, where the bug is still present, so it cannot catch what this PR fixes.

- **The test targets the wrong function.** The bug from issue #12 was in `invoice_total`, which used `paid >= due` on `main`. The PR fixes that by routing `invoice_total` through `late_fee`. But `late_fee` already had `paid > due` on `main`, and the PR doesn't touch it. `test_due_date_is_not_late` only calls `late_fee`, so it was already green before the fix.
- **Evidence:** The helper's base run put back `main`'s `billing.py`, and the check still passed. It flagged `test_due_date_is_not_late` as `PASSES there`. I also ran both versions in scratch folders. On `main`, `invoice_total(200.0, 2026-03-31, 2026-03-31)` returns `210.0`. On this PR's HEAD it returns `200.0`. The repo is unchanged.
- **Nothing in the suite covers the bug.** No test calls `invoice_total` with a payment on the due date. The existing `test_late_invoice_adds_fee` and `test_early_invoice_has_no_fee` both pass on `main` too.
- **Test to close it:** `invoice_total(200.0, date(2026, 3, 31), date(2026, 3, 31))` should equal `200.0`. This fails on `main` with `210.0`, and it would have caught the bug. Keep the `late_fee` test as well, since it covers the function the PR now depends on.

**Survivors (helper mutants that stayed green):**

- `billing.py:9`, `late_fee` rounds to 3 decimals instead of 2. This is a real gap. No test uses an amount with fractional cents. For example, a $10.01 invoice paid one day late should carry a fee of $0.50 (rounded to the cent), but the mutant returns $0.5005. Add `late_fee(DUE, date(2026, 4, 2), 10.01)` expecting `0.5`.
- `billing.py:15`, `invoice_total` rounds to 3 decimals instead of 2. This changes nothing observable. The inner `late_fee` already returns a two-decimal value, so the sum does not need a third decimal.

**What held:** The helper's 8 other mutants were caught, so the late-fee and early-payment behavior is covered. The suite's gap is the due-date path through `invoice_total`.

I changed nothing in the repo. The PR's "All tests pass" is true, but it doesn't show the fix works. I'd request changes on the test before approving.