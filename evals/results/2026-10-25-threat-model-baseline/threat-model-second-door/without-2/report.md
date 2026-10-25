I fixed SUP-88 and added tests that catch it. All 11 tests pass. Nothing is committed.

**Cause:** `invoices.export_csv` (`fixture/invoices.py:16`) took `customer_id` straight from the request body and never checked it against the logged-in user. The single-invoice view already had that check.

**Same hole on a second route:** `POST /integrations/accounting/pull` (`fixture/integrations/accounting.py`) calls the same function and only requires a login. Anyone who signs up could have pulled any customer's invoices through it as well. That matters with public signups opening next week.

**Fix:** I put the check inside `export_csv` itself, so both routes are covered and any future caller is too. It uses the same rule as `get_invoice`: customers can only export their own invoices, and staff can export anyone's.

```python
if customer_id != user.id and user.role != "staff":
    raise PermissionError("not your invoices")
```

That returns a 403. The nightly accounting sync logs in as staff, so it keeps working.

**Tests added** in `fixture/tests/test_app.py`:
- `test_export_others_refused`: reproduces the ticket. Alice sends `customer_id: 2` and gets a 403, with none of Bob's invoices in the response.
- `test_accounting_pull_refused_for_customers`: the same attack through the accounting route also gets a 403.
- `test_staff_can_export_any_customer`: staff can still export through both routes, so the sync doesn't break.

I removed the check temporarily and the first two tests failed, so they do catch the bug. With the check back in, everything passes.

The bug was exploitable until now, so it's worth checking request logs for export or accounting-pull calls where the `customer_id` doesn't match the caller. That tells you whether anyone besides the reporter used it.