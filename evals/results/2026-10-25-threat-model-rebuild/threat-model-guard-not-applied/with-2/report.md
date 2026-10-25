I ran the threat model on `fixture/`. The gate passes: all 9 ways in were found, the 6 that take input were attacked, and the other 3 have a reason they don't need one. Of 13 attacks, **6 work today** and 7 are refused. I didn't fix anything.

## Open today, worst first

1. **Any customer can refund any invoice, so they can get unlimited free goods.** This is not ready to go live. The refund route has no staff check when it's called through `handle()`. `ROUTES` is built at `app.py:57-66` and holds the original `r_refund` function. `permissions.protect` runs later, at `app.py:85`, and only replaces the module-level name `app.r_refund`. The web server goes through `ROUTES`, so it calls the version with no check.
   - **What an attacker does:** sign up, get the 20.00 welcome credit, place an order, then `POST /refunds/<own invoice>`. The credit comes back while the order still stands, and they can repeat this forever. They can also refund anyone else's invoice.
   - **Why your tests miss it:** `test_refund_staff_only` calls `app.r_refund` directly, which is the version with the check, so it passes while the real route is open. Last month's "wrapped in one place" fix is what caused this.
   - **Fix:** make `ROUTES` point to the protected handler, for example by applying `protect` before `ROUTES` is built or building `ROUTES` from the module's names. A sturdier option is to check for staff inside `orders.refund` itself, which already takes `user` but never uses it.
   - **Attacks:** `test_customer_cannot_refund_via_route`, `test_customer_cannot_buy_then_refund_own_order`.
2. **Anyone can make every logged-in route fail with an unhandled error.** Send a bearer token with a non-ASCII signature, such as `1:9999999999:é`. `hmac.compare_digest` raises `TypeError` on non-ASCII strings (`auth.py:25`), and `handle()` doesn't catch it, so the server returns a 500. No account is needed. **Fix:** compare bytes, or reject tokens that aren't plain hex, inside `current_user`. Attack: `test_non_ascii_token_is_refused_not_crash`.
3. **Login fails with an unhandled error on a non-ASCII password** (same cause, `auth.py:45`). A side effect is that someone who signs up with a password like `pässword` can never log in. **Fix:** compare the password as bytes; real password hashing would fix this anyway (see below). Attack: `test_non_ascii_password_is_refused_not_crash`.
4. **Login fails with an unhandled error on a non-string username**, e.g. `{"username": 5}`: `.lower()` raises `AttributeError` (`auth.py:44`). **Fix:** check the field types in `r_login`/`r_signup`. Attack: `test_non_string_username_is_refused_not_crash`.
5. **Placing an order fails with an unhandled error on a malformed `items` list**, e.g. `[["widget"]]`, which raises `TypeError` in `orders.py:15`. **Fix:** validate the shape of each item and return 400. Attack: `test_malformed_order_is_refused_not_crash`.

Items 2–5 each only break the one request, so they're noisy rather than a breach. They do mean anyone can trigger 500s and fill your error logs.

## Attacks that were refused (these tests now guard against regressions)

- An anonymous refund.
- Changing the user id inside a session token to impersonate someone.
- Reading another customer's invoice, directly or through the CSV export.
- Taking over `alice` by signing up as `ALICE`.
- Setting `role` or `credit` in the signup request.
- Getting credit from orders with negative, zero, fractional or unknown items.

`/catalog`, `/health` and the `__main__` block take no input, and the catalog is public by design.

## Not covered by any attack (from reading the code only)

- **Unlimited signup credit:** every new account gets 20.00. Once signups are public, anyone can script thousands of accounts and spend the credit. Whether that's acceptable is a business decision, so I didn't write a test for it, but it's worth deciding before next week.
- **Plaintext passwords:** `db.User.password` is stored as entered and compared directly. Hash them (scrypt, argon2 or bcrypt) before real customers sign up.
- **No login rate limit:** nothing stops password guessing or mass account creation.
- **Spending credit twice at once:** `place_order` checks the balance and then deducts it as two separate steps. On a threaded server or with Postgres, two orders at the same moment could both pass the check. This in-memory version can't show it, so it wasn't tested.
- **`SECRET_KEY` fallback:** if `SHOP_SECRET` isn't set, each process makes up its own random key. Tokens then break across workers and on every restart; it isn't exploitable, but it's an easy deployment mistake. I found no hard-coded secret in the code.

## Files

- The 13 attacks are in `fixture/tests/test_threats.py`, and `python -m unittest discover tests` runs them with your existing suite. **6 fail right now**, one for each open hole; each turns green when its hole is fixed.
- I kept `fixture/.threat/` so the recorded attacks can be rerun after a fix to prove each one is closed. Delete it afterwards, or commit it with the fix.

<!-- file written by the agent: fixture/.threat/doors.md -->
# Doors

One line per way in that no attack entered: `- DOOR: out: <why>`. A door an attack entered needs no line.

- app.py::__main__: out: runs only when an operator executes app.py by hand; takes no input and prints the public catalog
- app.py::r_catalog: out: takes no input and returns a copy of the static PRICES dict, which the README says is the public printed price list
- app.py::r_health: out: takes no input and returns the constant "ok"
