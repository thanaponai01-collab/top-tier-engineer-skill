SUP-88 is fixed and nothing is committed. Customers now get a 403 if they ask for another customer's invoices, and staff can still export anyone's. All 11 tests pass. I also put the old code back temporarily and checked that the new tests fail against it.

**Cause:** `export_csv` in `invoices.py` used whatever `customer_id` the request sent and never checked who was asking. The single-invoice view already had an owner-or-staff check; the export didn't.

**Fix** (`fixture/invoices.py`): `export_csv` now has the same check as `get_invoice`: you must own the invoices or be staff. I put the check in that function rather than in the route because a second route had the same hole. `POST /integrations/accounting/pull` only checked that someone was logged in, so any customer could call it with any `customer_id`. Both routes are now covered.

**Tests** (`fixture/tests/test_app.py`):
- `test_export_others_refused`: alice asking for bob's invoices (`customer_id: 2`) gets 403. This is the ticket's scenario, and it fails on the old code.
- `test_accounting_pull_refuses_customers`: a customer is refused on the accounting route, and staff still get the CSV. Also fails on the old code.
- `test_staff_can_export_any_customer`: staff can still export any customer. This passed before and after; it's there so the fix doesn't break the nightly accounting sync.

**Two other problems worth fixing before public signups (I didn't change these):**
- **Free credit for every signup.** Each new account gets a 20.00 welcome credit (`settings.SIGNUP_CREDIT`) that pays for real orders. There's no limit on signups, so anyone can script accounts and order goods for free.
- **Passwords are stored and compared in plain text** (`db.User.password`, `auth.login`). They should be hashed, for example with bcrypt or argon2, before real customers sign up.