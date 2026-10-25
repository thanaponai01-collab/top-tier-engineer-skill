I ran the threat model on `fixture/`, and you shouldn't open signups as the code stands. A customer account, or in some cases anyone at all, can get free goods and unlimited store credit, read other customers' invoices, and take over existing accounts, including the staff account.

I found 9 ways in and attacked 7 of them with tests. 9 attacks got through and 3 were refused. Each one is a test in `fixture/tests/test_threats.py` that passes only when the abuse is refused. I haven't fixed anything.

## Open today, worst first

1. **Free goods and unlimited credit** (`POST /orders`, `orders.py:15-23`). Any customer can send a negative `qty`. It goes into the total unchecked, and the credit check passes because the total is below zero. One order of `gizmo, qty -100` adds 450 in credit. Adding a negative line to a real order ships the real items: 10 gadgets (199.90) on 5.00 credit worked.
   - Fix: in `place_order`, refuse any quantity below 1, and refuse any total of zero or less.
   - Tests: `test_negative_quantity_cannot_mint_credit`, `test_negative_line_cannot_pay_for_real_goods`.
2. **Taking over accounts, including staff** (`POST /signup`, `auth.py:35-39`). Signup checks whether the name exists as typed, but saves it in lower case. Signing up as `Alice` replaces the real alice: the attacker logs in as `alice` with their own password, and alice is locked out. Doing the same with `SAM` locks the only staff account out of refunds.
   - Fix: lower-case the name once at the start of `signup`, and run the "taken" check on that.
   - Tests: `test_signup_with_other_case_cannot_take_over_account`, `test_signup_with_other_case_cannot_displace_staff`.
3. **Anyone can read every customer's invoice history** (`POST /invoices/export`, `app.py:47`). `customer_id` is taken straight from the request body, and `export_csv` never checks it against the logged-in user. Alice downloaded bob's invoices.
   - Fix: in `export_csv`, allow it only when `customer_id` is the user's own id or the user is staff, the same rule `get_invoice` already uses.
   - Test: `test_export_other_customers_invoices_refused`.
4. **Fake staff logins from the source code** (`settings.py:1`). The key that signs session tokens is written directly in the source. Anyone who has seen the code (repo access, a leaked backup, a former contractor) can make a valid token for any user id. With a forged staff token the test issued a refund, and the same token can read every invoice.
   - Fix: rotate the key, and load it from the environment or a secret store at startup so it's no longer in the code.
   - Test: `test_token_signing_key_from_source_cannot_forge_staff`.
5. **Unlimited password guessing** (`POST /login`). Nothing slows down or limits failed logins: after 50 wrong guesses, the 51st still logged in. Passwords are also stored in plain text (`db.User.password`), and signup accepts a 1-character password.
   - Fix: limit failed logins per account and per IP in `auth.login`, and store salted hashes (scrypt or argon2).
   - Test: `test_password_guessing_is_throttled`.
6. **Bad requests crash instead of being rejected** (`app.py:72-76`). Sending `items` as a string throws a TypeError, and `GET /invoices` without an id throws an IndexError. Both escape `handle()`, so the web server returns 500s that anyone logged in can trigger.
   - Fix: check the shape of `items` in `place_order`, and have `r_invoice` and `r_refund` reject a missing id with a 400.
   - Tests: `test_malformed_items_get_a_clean_error`, `test_invoice_without_id_gets_a_clean_error`.

## Refused (3)
- Reading another customer's invoice through `GET /invoices/<id>`.
- A customer refunding their own order, and staff refunding the same invoice twice.
- Changing prices by editing the catalog response (it returns a copy).

## Doors I didn't attack
- `GET /health` only returns a fixed "ok" and touches no data.
- The `__main__` block in `app.py` only runs when someone executes the file by hand, and sends one fixed request.

## What this didn't cover
- **Race conditions:** two orders at the same moment could spend the same credit twice, since nothing locks it. I only read this; I didn't test it.
- **Tokens:** they can't be revoked (there's no logout), and they stay valid for an hour after a password change.
- **The real database:** the Postgres swap mentioned in `db.py` isn't in this code.
- **Everything outside the code:** the web server, TLS, dependencies, and how the app is deployed.

## Where things stand
- **The suite now fails on purpose.** `python -m unittest discover tests` shows 9 failures, one per open issue. It turns green as each fix lands, and fails again if a later change reopens one.
- **`.threat/` is still in `fixture/`.** After a fix, the gate uses it to confirm each attack is now refused. Delete it once that's done, or commit it with the fix.
- **Next step:** if you want me to fix these, I'd start with items 1–4.

<!-- file written by the agent: fixture/.threat/doors.md -->
# Doors

One line per way in that no attack entered: `- DOOR: out: <why>`. A door an attack entered needs no line.

- app.py::__main__: out: runs only when an operator executes app.py by hand; it sends one fixed GET /catalog and takes no outside input
- app.py::r_health: out: ignores headers, body and args and returns the constant "ok"; it reads and changes no state
