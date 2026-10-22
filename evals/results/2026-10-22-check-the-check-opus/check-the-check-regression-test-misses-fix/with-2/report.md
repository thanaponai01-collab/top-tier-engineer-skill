No. The regression test doesn't prove the bug is fixed. It passes on the old, buggy code too, so it would never have caught issue #12.

**Why:** the bug was in `invoice_total`. On `main` it worked out its own fee with `paid >= due`, which charged a fee on the due date. `late_fee` already used `paid > due` and was correct. The PR fixes this by making `invoice_total` call `late_fee`, which is the right change. But the new test, `test_due_date_is_not_late`, only calls `late_fee(DUE, DUE, 200.0)`, and that function was never broken.

**What I ran:**
- **Old code:** I ran the PR's tests against `main`'s `billing.py`. All 5 pass there, including the new test. So CI being green says nothing about #12.
- **Direct check of old code:** `invoice_total(200.0, 2026-03-31, 2026-03-31)` on `main` returns **210.0**, which is exactly the bug in the report. `late_fee` on the same input returns 0.0.
- **The missing test:** call `invoice_total(200.0, DUE, DUE)` and expect `200.0`. That fails on `main` (210.0) and passes with this PR. No test currently calls `invoice_total` with a due-date payment.

**Other gaps from the planted bugs (10 one-line bugs, 8 caught):**
- **Rounding in `late_fee` (`billing.py:9`):** changing it from cents to 3 decimals went unnoticed. This is a real gap. A late $333.33 invoice should have a fee of $16.67, but $16.666 would also pass. A late test with an amount that doesn't divide evenly would close it.
- **Rounding in `invoice_total` (`billing.py:15`):** the same change went unnoticed here. It makes no visible difference as long as amounts are whole cents, because the fee is already rounded to cents.

**What the tests do catch:** a late payment adding a 5% fee, and an early payment costing nothing, in both functions. Planted bugs in those parts were caught.

The code change is fine. I'd ask for the `invoice_total` due-date test before approving, because that's the test that actually covers #12. Nothing in the repo was modified; all runs were in scratch copies. If you want that test written and checked against both versions, the `verify-loop` skill can do it.