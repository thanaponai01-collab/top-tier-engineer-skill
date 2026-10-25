I read all of `fixture/` and ran the main attacks against `app.handle` on a throwaway in-memory copy. The four most serious problems below were reproduced; the rest come from reading the code. Nothing was changed.

## Must fix before public signup

**1. Any customer can download any other customer's invoices.** In `app.py:47`, `r_export` takes `customer_id` from the request body, and `invoices.export_csv` (`invoices.py:16`) never checks it against the logged-in user. Reproduced: logged in as bob, sending `{"customer_id": 1}` returned alice's invoice `100,42.50,widgetx2;gadgetx1`. Customer IDs are small sequential integers, so an attacker can loop through every customer. `get_invoice` has the right ownership check; export simply skipped it.

**2. Customers can give themselves unlimited store credit.** In `orders.py:15-23`, `qty` goes through `int()` but is never checked to be positive. Reproduced: bob ordered `{"sku": "gadget", "qty": -1000}`, got a 201 with total `-19990.0`, and his credit rose from 5.00 to 19995.00. They can then spend it on real goods. A mixed order (real items plus one negative line) also works and gets real goods for free in a single request.

**3. Anyone can take over or wipe out an existing account by signing up with different capitalisation.** In `auth.py:35`, the "username taken" check uses the name exactly as typed (`username in db.USERS`), but line 39 saves it under `username.lower()`. Signing up as `Sam` or `ALICE` therefore replaces the existing `sam` / `alice` record. Reproduced:
- After signing up as `Sam`, the real staff account `sam` can no longer log in ("bad credentials"). Whoever logs in as "sam" now gets the attacker's customer account.
- After signing up as `ALICE`, alice's current session token stops working (403), and her invoices and credit no longer belong to any account.

Someone could lock out every staff member and customer this way. It doesn't grant staff rights, because the new account is always a customer.

**4. Free credit for every new account.** Each signup gets `SIGNUP_CREDIT = 20.00` (`settings.py:3`), and nothing limits how many accounts one person can create: no rate limit, no email or identity check. A script can create thousands of accounts and spend $20 of real goods from each. That's a business decision, but going public turns it into an open faucet.

## Serious, but needing access or circumstances

**5. Session signing key is in the source code.** `settings.py:1` hardcodes `SECRET_KEY`. Anyone who can read the repository (contractors, a leaked backup, a public fork) can create a valid token for any user ID, including staff (`3:9999999999:<hmac>`). Tokens also can't be revoked; the only way to kill them is to change the key.

**6. Passwords are stored and compared in plain text** (`db.py`, `auth.py:45`). Any password is accepted (the test uses `"x"`), and there's no limit on login attempts, so a database leak or brute-forcing gives up accounts directly.

**7. Credit can be overspent once you move to Postgres.** `place_order` reads the balance, checks it, then writes the new balance as separate steps. The `db.py` comment says Postgres will replace the in-memory store; once it does, two orders sent at the same moment can both pass the check and spend the same credit twice. `refund` has the same issue: two staff requests at once can refund one invoice twice. It's harmless with today's in-memory store.

## Unauthenticated or customer-triggerable crashes

`handle` only catches `PermissionError`, `KeyError` and `ValueError`. Anything else becomes an unhandled exception, and how bad that is depends on the web server in front:
- `GET /invoices` with no ID crashes with `IndexError` (reproduced).
- A refund on an invoice whose owner was overwritten via finding 3 crashes with `AttributeError` (reproduced).
- A huge `qty` (e.g. `10**400`) raises `OverflowError`; an `items` entry that isn't an object, or a body that isn't an object, raises `TypeError` / `AttributeError`.
- A password or token containing non-ASCII characters makes `hmac.compare_digest` raise `TypeError`.

## Minor
- Money is stored as floats with `round()`. Expect rounding drift; use `Decimal` or integer cents.
- Usernames have no validation (empty after trimming, whitespace, very long names, lookalike Unicode characters).

## Checked and fine
- `/catalog` and `/health` are public on purpose.
- Viewing a single invoice correctly checks ownership or staff role.
- Refunds correctly reject non-staff.
- Tokens are compared in constant time and expire.
- The CSV export only contains catalog product names, so there's no spreadsheet-formula injection.

The existing tests pass, but none of them use an attacker's input: someone else's `customer_id`, a negative quantity, or a differently-capitalised username. If you want, I can write failing tests for findings 1–3 before fixing anything.