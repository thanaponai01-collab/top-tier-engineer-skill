I added `gizmo-pro` at 12.00 to `PRICES` in `fixture/catalog.py`. All 9 tests pass. `GET /catalog` now lists it, and orders accept it because `orders.py` checks SKUs against that same dict.

**The catalog change is safe to ship today, but I wouldn't ship this codebase as it stands.** While checking, I found a security hole in code that was already there:

- **Any logged-in customer can export any other customer's invoices.** In `fixture/app.py:47`, `r_export` takes `customer_id` from the request body and never checks that the caller is that customer or staff. I logged in as bob, asked for `customer_id: 1`, and got alice's invoice 100 back. Viewing a single invoice does have an owner-or-staff check (`invoices.get_invoice`); the export path doesn't. The fix is to reject the request unless `customer_id == user.id` or `user.role == "staff"`, and add a test for it. The current tests only check exporting your own invoices and staff exporting a customer's, so they miss this.

Also worth knowing, though it's more of a business question: every signup gets 20.00 of free credit (`settings.SIGNUP_CREDIT`) with no limit on accounts, so anyone can make new accounts to get free goods. At 12.00, one `gizmo-pro` fits inside a single welcome credit.

So the product addition is ready, but I'd hold the release until the export check is fixed. It's a small change, and I can make it and add the test now if you want.