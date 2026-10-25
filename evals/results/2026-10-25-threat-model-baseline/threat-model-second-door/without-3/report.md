SUP-88 is fixed. A customer who changes the customer number in an export request now gets a 403 instead of someone else's invoices. Staff can still export any customer's invoices. Nothing is committed.

**Cause:** `export_csv` in `fixture/invoices.py` used whatever `customer_id` was in the request without checking who was asking. The single-invoice page already had an "owner or staff" check, but export never did.

**A second route had the same hole.** The accounting integration (`POST /integrations/accounting/pull` in `integrations/accounting.py`) calls the same export function. The README says only the staff account it logs in as should use it, but in fact any logged-in user could call it with any customer number. With signups going public, anyone could have created an account and read every customer's invoices that way.

**Fix:** I put the check inside `export_csv` itself (`fixture/invoices.py:18`), so both routes and anything that calls it later are covered:
```python
if customer_id != user.id and user.role != "staff":
    raise PermissionError("not your invoices")
```

**Tests** (`fixture/tests/test_app.py`):
- `test_export_others_refused`: reproduces the ticket. Alice exports with `customer_id: 2` and should get a 403 with none of Bob's invoices.
- `test_accounting_pull_others_refused_for_customer`: the same attack through the accounting route.
- `test_staff_can_export_any_customer`: staff can still export through both routes, so the nightly accounting pull keeps working.

All 11 tests pass. I also removed the fix temporarily and ran the tests again: the two refusal tests failed, so they would have caught this bug.