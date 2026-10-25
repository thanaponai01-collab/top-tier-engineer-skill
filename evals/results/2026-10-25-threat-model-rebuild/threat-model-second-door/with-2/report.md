SUP-88 is fixed, and the threat model found a second way to reach the same leak, which the same fix closes. Nothing is committed.

## The fix

Before the fix, any logged-in customer could read any other customer's invoices in two ways:
- **`POST /invoices/export`** (`fixture/app.py:47`): this is SUP-88. The export used whatever `customer_id` was in the request and never checked whose it was.
- **`POST /integrations/accounting/pull`** (`fixture/integrations/accounting.py:7`): this is the route the nightly accounting sync uses. It only checked that the caller was logged in, not that they were staff. Once signups are public, anyone could create an account and pull every customer's invoices this way.

Both routes go through `invoices.export_csv`, so that's where I put the check (`fixture/invoices.py:18`). It uses the same rule `get_invoice` already has: you can only export your own customer number unless you're staff. Customers can still export their own invoices and the accounting sync (logged in as staff) still works; tests cover both.

## Tests: `fixture/tests/test_attacks.py`

The helper confirmed each new test failed on the old code, passes now, and fails again if `invoices.py` is put back:
- `test_export_other_customers_invoices_refused`: the test for SUP-88.
- `test_customer_cannot_use_accounting_pull`

These other attacks were already refused before my change, and each is now a test:
- editing the user ID inside a login token
- using a negative quantity in an order to gain credit
- a customer refunding their own order, or a double refund
- signing up as `ALICE` to take over `alice`, or giving yourself the staff role at signup
- logging in with the wrong password
- reading an invoice without logging in

The full suite passes (18 tests). `/catalog`, `/health` and the `__main__` block weren't attacked: they take no input and return data that's meant to be public.

## Not fixed: worth a look before public signups
1. **Free credit at signup:** every new account gets $20 of store credit (`settings.SIGNUP_CREDIT`). With open signups, a script can create accounts and order real goods for free. That's a product decision (limit it, verify accounts, or drop it), so I didn't change it.
2. **Passwords stored in plain text** (`fixture/db.py`): they should be hashed before real users arrive.
3. **Crash on non-ASCII password:** logging in with something like `é` makes `hmac.compare_digest` raise a `TypeError` that nothing catches, so the request crashes instead of returning 401. I confirmed this. A forged token with non-ASCII characters in its signature would crash the same way. `GET /invoices` with no ID also crashes, with an uncaught `IndexError`. These give an attacker nothing beyond error responses.
4. **Session key:** if `SHOP_SECRET` isn't set, a random key is used, so sessions break on restart and across multiple servers. Set it in production.

**Not covered:** I only read the code for configuration, dependencies, behaviour when requests run at the same time, and the real Postgres layer the README mentions. No attacks were run against them. I also didn't look at the web server in front of `handle()`.

I deleted the helper's `.threat/` folder and kept the attack tests.