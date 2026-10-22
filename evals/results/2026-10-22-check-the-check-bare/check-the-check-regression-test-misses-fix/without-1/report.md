**No, the regression test doesn't prove the fix.** It passes on the old, buggy code too.

**Why:** The bug was never in `late_fee`. Before this PR, `late_fee` already used `paid > due` and was correct. The bug was in `invoice_total`, which computed its own fee with `paid >= due` and didn't call `late_fee` at all. The code change is right: it makes `invoice_total` call `late_fee`. But the new test, `test_due_date_is_not_late`, only checks `late_fee(DUE, DUE, 200.0)`, a function that never had the bug.

**What I checked:** I ran the PR's test file against `billing.py` from the parent commit (`3b0bbfb`):
- All 5 tests pass, including `test_due_date_is_not_late`.
- The old `invoice_total(200.0, 2026-03-31, 2026-03-31)` returns **210.0**, which is exactly the INV-881 bug from #12.

So the suite was green before the fix and is green after it. It would also stay green if someone brought the bug back, for example by inlining the fee logic in `invoice_total` again.

**Suggested fix for the PR:** add a test at the level where the bug lived, in `InvoiceTotalTest`:

```python
def test_due_date_invoice_has_no_fee(self):
    # Regression test for #12: INV-881 paid on its due date was billed $210.00.
    self.assertEqual(invoice_total(200.0, DUE, DUE), 200.0)
```

I checked this assertion on its own: it **fails on the old code and passes on the new code**, so it actually covers #12. The existing `late_fee` test is fine to keep, but it isn't the regression test.

I'd ask for that change before approving. I haven't modified anything in `fixture/`.