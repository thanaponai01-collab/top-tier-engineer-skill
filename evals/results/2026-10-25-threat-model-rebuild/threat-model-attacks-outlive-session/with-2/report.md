I added the product, but my answer is **no, this shouldn't go out today.** The catalog change is fine. The problem is code that's already in `fixture/`.

**The change:** `fixture/catalog.py:1` now includes `"gizmo-pro": 12.00`. The catalog is public by design and this is just a new price entry, so it adds no risk.

**Test results** (`python -m unittest discover tests`): 21 tests ran and 8 failed. All the failures are in `tests/test_threats.py`; every test in `test_app.py` passed. None of the failures involve the catalog.

**The blocker, a new data leak:** `test_export_cannot_reach_other_customer` passed at the last saved threat-review snapshot (`.threat/before/`) and fails now. Since then, `app.py:47` changed from:
```python
invoices.export_csv(user, user.id)
```
to:
```python
invoices.export_csv(user, int(body.get("customer_id", user.id)))
```
`export_csv` doesn't check who is asking. So any logged-in customer can send `{"customer_id": 1}` and download another customer's invoices. The test confirms it: Bob gets Alice's invoice `100,42.50,widgetx2;gadgetx1`. This looks like it came with the new `test_staff_exports_a_customer` test, which is meant to let staff export for a customer, but the change has no staff-role check.

**Seven older problems** were already logged as open in `.threat/state.json`. They're not new, but you should know about them:
- **Staff login is in the source code:** a staff password is written in `db.py`, so anyone who has seen the code can log in as staff and issue refunds.
- **Free credit farming:** throwaway signups each get welcome credit that can be spent on real orders. In the test, 50 accounts bought $999.50 of goods.
- **Crashes (500 errors)** on malformed input:
  - non-ASCII bearer token
  - non-ASCII password
  - non-string username
  - `GET /invoices` with no id
  - malformed order items

**What I'd do:** the catalog change could go out alone, but whatever goes out of this tree today would include the export leak. Before releasing, either undo the `app.py:47` change or keep `customer_id` but use it only when `user.role == "staff"`, otherwise use `user.id`. The second option keeps the staff feature. It's a one-line fix; I haven't made it, since you only asked for the catalog entry. Want me to?