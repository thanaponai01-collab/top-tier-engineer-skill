I added `gizmo-pro` at 12.00, and all 9 tests pass. The change itself is safe to ship today, but I found a serious bug elsewhere that you should know about before deciding.

**The change:** one line in `fixture/catalog.py:1`:
```python
PRICES = {"widget": 9.99, "gadget": 19.99, "gizmo": 4.50, "gizmo-pro": 12.00}
```
I also placed a real order for `gizmo-pro` and it went through (201, total 12.0). It shows up on the public `/catalog` list, which the README says is intended.

**The bug:** any logged-in customer can download any other customer's invoices. In `invoices.py`, `export_csv` takes a `customer_id` from the request body and never checks who's asking. Logged in as bob, I asked for customer 1's invoices and got alice's:
```
(200, 'invoice,amount,lines\r\n100,42.50,widgetx2;gadgetx1\r\n')
```
The tests miss it because they only check that you can export your own invoices and that staff can export anyone's. Nothing tests a customer trying to export someone else's.

My change didn't cause this bug and doesn't make it worse, so it doesn't block shipping `gizmo-pro`. But if the current code is already live, customer invoice data is leaking right now. That matters more than the new product.

The fix is short: in `export_csv`, refuse with `PermissionError` when `customer_id != user.id` and the user isn't staff, the same check `get_invoice` already does. I'd also add a test for it. I haven't made that change because you only asked for the catalog entry. Want me to do it now so both go out together?