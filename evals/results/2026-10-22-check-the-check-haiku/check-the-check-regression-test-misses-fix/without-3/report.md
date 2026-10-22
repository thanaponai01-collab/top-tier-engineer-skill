**No. The regression test passes on the buggy code, so it doesn't prove the fix.**

The bug was in `invoice_total`, which charged a fee when `paid >= due`. The PR fixes that by delegating to `late_fee`, which already used `paid > due`. But `test_due_date_is_not_late` only calls `late_fee(DUE, DUE, 200.0)`, and that function was already correct before this PR.

I checked by running the tests in temp copies of each commit:

- **Parent commit (`3b0bbfb`), buggy code:** `invoice_total(200.0, 2026-03-31, 2026-03-31)` returns **210.0**. That reproduces issue #12.
- **New test run against the buggy `billing.py`:** `test_due_date_is_not_late` **passes**. It can't fail on the bug it's named for.
- **PR commit (`73ae017`):** the fix works. The same call returns 200.0.

So the fix itself is right, but nothing in the suite would catch a regression in `invoice_total`. The existing `InvoiceTotalTest` cases cover only a late payment and a payment in March, not the due date.

**Suggested fix:** add a test that goes through the path the customer hit:

```python
def test_due_date_invoice_has_no_fee(self):
    self.assertEqual(invoice_total(200.0, DUE, DUE), 200.0)
```

I expect this to fail on the parent's `billing.py` and pass on the PR's, which would make it a real regression test. I haven't changed anything in the repo. Do you want me to add that test to the branch and rerun the suite against both commits to confirm?