Nine attacks work today and eight were refused. The worst one undoes last month's main fix: **any signed-up customer can issue refunds**, which the staff-only check was meant to stop. The helper's gate finished (`THREAT-GATE: done`). I changed no application code.

## What works today, worst first

1. **Any customer can refund any invoice** (`app.py:57-85`). `ROUTES` stores the original `r_refund` function when the module loads. Line 85 then replaces `app.r_refund` with a staff-checked version, but `ROUTES` still holds the old, unchecked one. So `POST /refunds/<id>` only checks that someone is logged in. For example, bob refunded alice's invoice 100 and alice's credit went from 50 to 92.50.
   - Your existing `test_refund_staff_only` passes because it calls `app.r_refund` directly, not through `handle()`. That's why this got through.
   - **Fix:** put the staff check where the route is registered (or inside `orders.refund` itself), and test it through `handle()`.
2. **Unlimited free goods through refunds.** Same cause: a customer orders, refunds their own invoice, gets the credit back, and repeats. The money check in `place_order` doesn't help, because the credit keeps coming back.
3. **Unlimited welcome credit for anyone** (`auth.signup`). Signup is open and every new account gets `SIGNUP_CREDIT` (20.00) to spend on real goods. 50 scripted signups gave out 1,000.00. This is a business decision, not a coding mistake. The fix is to give the credit only after something a script can't easily repeat (email or payment verification, one per customer), or to drop it before signups open. My test assumes the credit shouldn't be farmable. Change that test if you decide otherwise.
4. **Anyone can crash requests with bad input.** Each of these raises an exception that `handle()` doesn't catch, so it reaches your web server as an error (probably a 500):
   - **No account needed:**
     - an `Authorization: Bearer 1:9999999999:é` header (`hmac.compare_digest` rejects non-ASCII text, `auth.py:25`)
     - logging in with a non-ASCII password or a number as the password (`auth.py:45`)
     - signing up with a username that isn't text (`auth.py:35`)
   - **Customer account:**
     - an order item that isn't an object (`orders.py:15`)
     - `GET /invoices` with no id (`app.py:44`)
   - A side effect: someone who signs up with a non-ASCII password can never log in.
   - **Fix:** check the types in the handlers, compare bytes in `compare_digest`, and have `handle()` turn any other error into a plain 400/500.

## Refused (attacked, came out OK)
- Refunding without logging in
- Forging a token with your own signature to act as staff (sam)
- Extending a token's expiry
- Signing up as `SAM` to take the staff name
- Ordering a negative quantity
- Spending more than your credit
- Reading another customer's invoice
- Exporting another customer's invoices (the export ignores any customer id sent in the request)

## Doors I didn't attack
I didn't attack `/catalog` (public by design per the README), `/health` (returns a fixed "ok"), or the `__main__` block (only runs when someone executes `app.py` by hand). None of them takes input or returns anything that isn't already public.

## Not covered
I only read these, without attacking them:
- **Passwords are stored in plain text** (`db.py`). Combined with no password rules and no login rate limit, accounts are easy to brute-force.
- **The token secret:** if `SHOP_SECRET` isn't set, each process makes up its own key. Tokens then stop working after a restart or on a different worker. That breaks logins but isn't an exploit.
- **Concurrency:** the credit check and the deduction in `place_order` aren't one atomic step. That would matter once this runs on Postgres with several workers.

No secrets are hard-coded in the source. Dependencies and deployment config weren't in scope.

## Files I added
- `fixture/tests/test_attacks.py` has the 17 attack tests and runs with your normal `python -m unittest discover tests`. The 9 open attacks fail until they're fixed, so the suite will be red until then. Your original 8 tests still pass.
- `fixture/.threat/` is the helper's record of the attacks. I left it so it can check later that each fix closes its attack. Delete it, or commit it with the fixes.

<!-- file written by the agent: fixture/.threat/doors.md -->
# Doors

One line per way in that no attack entered: `- DOOR: out: <why>`. A door an attack entered needs no line.

- app.py::__main__: out: runs only when an operator executes app.py by hand; it takes no input and prints the public catalog
- app.py::r_catalog: out: takes no input and returns a copy of PRICES, which the README says is the public printed price list
- app.py::r_health: out: takes no input and returns the constant "ok"
