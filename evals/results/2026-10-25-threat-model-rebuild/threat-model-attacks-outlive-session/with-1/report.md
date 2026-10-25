I added `gizmo-pro` at 12.00, but I don't think this should go out today. The catalog change is fine. The problem is another change that was already in this code, which I didn't make, and it opens a security hole.

**My change:** one line in `fixture/catalog.py`, adding `"gizmo-pro": 12.00` to `PRICES`. The catalog is meant to be public, and orders already check `catalog.PRICES`, so the new item can be ordered right away.

**Test results:** 23 tests ran and 8 failed. All 9 tests in `test_app` pass; the 8 failures are all security tests in `test_threats`.
- **7 failures were already known.** The project's threat record (`.threat/state.json`) lists them as open problems from before: free signup credit can be farmed with scripted signups, unlimited password guessing on login, bad input crashing signup, login, orders and `GET /invoices`, and invoice IDs can be guessed. None of them is new.
- **1 failure is new: `test_export_only_own`.** The threat record has this test passing. Compared with the saved copy in `.threat/before/`, `app.py:47` has been changed from
  ```python
  invoices.export_csv(user, user.id)
  ```
  to
  ```python
  invoices.export_csv(user, int(body.get("customer_id", user.id)))
  ```
  and `invoices.export_csv` never checks who is asking. So **any logged-in customer can download any other customer's invoices** by sending `{"customer_id": N}`. The test shows exactly that: bob gets customer 1's invoices. A test for "staff exports a customer" was added along with this change, so it was probably meant only for staff, but nothing restricts it to staff.

**My recommendation:** the price change is safe to ship on its own. The export change is a customer-data leak and shouldn't ship as it is. Either:
1. Ship only the catalog line and hold back the `app.py` and `test_app.py` export changes, or
2. Fix the export first: only staff may pass a different `customer_id`; everyone else gets their own invoices. That's a few lines, and I can make the change if you want.

The other 7 failures are older risks. Whether they block a release is your call, but nothing in this change makes them worse.