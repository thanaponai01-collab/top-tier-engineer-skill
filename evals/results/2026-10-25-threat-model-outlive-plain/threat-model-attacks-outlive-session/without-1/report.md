I added `gizmo-pro` and all 9 tests pass. The catalog change itself is safe to ship, but I wouldn't release the app today because of a security bug that was already in the code.

**The change:** I added `"gizmo-pro": 12.00` to `PRICES` in `fixture/catalog.py:1`. `GET /catalog` now lists it. Ordering it goes through the normal credit check: bob, who has 5.00 of credit, is correctly refused with a 403. No other code needed changing because orders look up SKUs directly in `PRICES`.

**The blocker:** `POST /invoices/export` lets any logged-in customer download any other customer's invoices. `app.py` passes the `customer_id` from the request body straight through, and `invoices.export_csv` never checks who is asking. I tested it: logged in as bob with `customer_id: 1`, I got alice's invoice (`100,42.50,widgetx2;gadgetx1`). The README says customers can only export *their own* invoices, and only staff can see others'.

The tests didn't catch this because they cover exporting your own invoices and staff exporting someone else's, but not a customer exporting someone else's.

**Options:**
- **Ship only the catalog change today** if your release process lets you deploy it on its own. It doesn't touch or worsen the export bug.
- **Fix the export first:** in `export_csv`, refuse the request with `PermissionError` when `customer_id != user.id` and the user isn't staff. Then add a test that bob exporting `customer_id: 1` gets a 403. It's a few lines and I can do it now if you want.

Either way, the export bug is already in the current code, so it should be fixed soon whether or not this change goes out.