The test doesn't prove the bug is fixed. I checked this by running it against the old code.

**Why:** The bug was in `invoice_total`. Before the fix it calculated its own fee with `paid >= due`, so a payment made on the due date got charged. `late_fee` already used `paid > due` and was correct before the PR. The new `test_due_date_is_not_late` only calls `late_fee(DUE, DUE, 200.0)`, so it tests code that was never broken.

**What I ran:** I put the pre-fix `billing.py` (commit `3b0bbfb`) next to the PR's `test_billing.py`:
- All 5 tests pass, including the new regression test.
- On the old code, `invoice_total(200.0, 2026-03-31, 2026-03-31)` returns **210.0**. That's the exact bug from issue #12.

So the test passes whether or not the bug is there. If someone brought back the `>=` logic in `invoice_total`, CI would stay green.

**The code change itself is fine.** Having `invoice_total` call `late_fee` removes the duplicate calculation where the bug lived. Only the test is wrong.

**Suggested fix:** add a test that checks the amount the customer was actually billed, in `InvoiceTotalTest`:

```python
def test_due_date_invoice_has_no_fee(self):
    # Regression test for #12: INV-881 paid on its due date was billed 210.00.
    self.assertEqual(invoice_total(200.0, DUE, DUE), 200.0)
```

This fails on the old code (210.0 ≠ 200.0) and passes with the fix. You can keep the existing `late_fee` test as a boundary check, but its comment shouldn't call it the regression test for #12.

I'd ask for this change before approving.