The biggest problem: **any logged-in customer can issue refunds.** The staff-only check that last month's fixes added never runs on real requests. I confirmed this by running it against the code (I didn't change anything), and the test suite still passes.

## 1. Critical: the staff check on refunds is bypassed

`app.py:57-66` builds `ROUTES` with direct references to the handler functions. Later, `app.py:84-85` calls `permissions.protect(...)`, which swaps `app.r_refund` for the wrapped, staff-checked version. `ROUTES` still points at the original, unchecked function, so `handle()` never calls the guarded one. `r_refund` only calls `_need_user`, which accepts any logged-in user.

What I ran:
- `ROUTES[("POST","refunds")] is app.r_refund` → `False`
- Bob (a customer) sent `POST /refunds/100`, which is Alice's invoice, and got `200`. Alice's credit went from 50 to 92.50.
- A brand-new signup ordered a gadget, refunded the order itself, and repeated that 3 times. Each time it got the goods and kept its full $20 credit. Whatever you ship against an invoice is effectively free.
- Any customer can also refund anyone else's invoices (IDs run in sequence from 1000, so they're easy to guess). That zeroes those invoices and adds credit to the owners' accounts.

Why the test didn't catch it: `test_refund_staff_only` calls `app.r_refund(...)` directly, which is the wrapped version. It never goes through `app.handle`, which is the path real requests take. The comment saying this "can't forget its check" is wrong because of the order things happen in.

## 2. High: free credit from unlimited signups
`/signup` has no rate limit, email check or CAPTCHA, and each account gets `SIGNUP_CREDIT = 20.00`. Someone with a script can create thousands of accounts and spend $20 of free goods from each. Once signups open, this is a direct money leak even after #1 is fixed.

## 3. Medium: bad input from anyone causes server errors
`handle()` only catches `PermissionError`, `KeyError` and `ValueError`. These requests all raised errors that nothing caught:
- **No login needed:** `Authorization: Bearer 1:9999999999:é` crashes because `hmac.compare_digest` raises `TypeError` on non-ASCII text (`auth.py:25`). That happens on every authenticated route.
- **No login needed:** `POST /login` with a non-ASCII password (`auth.py:45`) gives a `TypeError`. A side effect: anyone who signs up with a non-ASCII password can never log in.
- **No login needed:** `POST /login` or `/signup` with a non-string username, e.g. `{"username": 1}`, gives an `AttributeError`.
- `GET /invoices` with no ID gives an `IndexError` (`app.py:44`).
- An `items` value that isn't a list of objects (e.g. `"ab"`, or a list as the `sku`) gives a `TypeError` (`orders.py:15-18`).

What a user sees depends on your web server: at best a 500 with a stack trace, at worst a worker that dies.

## 4. Medium: race conditions once requests run concurrently
These need a threaded server or Postgres with several workers to matter.
- **Spending credit twice** (`orders.py:23-25`): the code checks the credit balance and deducts it as separate steps with no lock or transaction. Two orders sent at the same time can both pass the check and spend the same credit twice.
- **Duplicate user IDs** (`auth.py:37`): new IDs are `max(id)+1`, which isn't atomic. Two simultaneous signups can get the same ID. Tokens hold only the ID and `user_by_id` returns whichever account it finds first, so one user could end up logged in as the other.
- **Double refunds** (`orders.py:33-38`): the refund also checks and then updates in separate steps, so two simultaneous refunds of the same invoice can both pay out.

## 5. Lower-severity issues to note before launch
- **Passwords are stored in plain text** (`db.py`, `auth.py:45`). Any leak of the database or a backup exposes every customer's password. There's also no minimum password rule (`"x"` is accepted) and no limit on login attempts, so passwords can be guessed by brute force.
- **Tokens can't be revoked.** There's no logout, and changing a password doesn't invalidate existing tokens. A stolen token works for the full hour.
- **Signing key fallback** (`settings.py:4`): if `SHOP_SECRET` isn't set, each process generates its own random key. With several workers, a token from one worker fails on another, and every restart logs everyone out. That's not a breach, but it may push someone to set a weak shared secret in a hurry.
- **Usernames that look alike:** usernames are compared with `.lower()` only and no Unicode normalisation, so names like `аlice` (with a Cyrillic а) can impersonate real users.
- **Login timing reveals which usernames exist** (`auth.py:45`): an unknown username returns faster than a wrong password.

## What looked fine
- Viewing invoices checks the owner or staff role correctly.
- Export always uses the caller's own ID.
- Signup can't set `role`.
- Token signatures are verified with a constant-time comparison.
- Order quantity and SKU are validated.
- `/catalog` and `/health` are public, as the README says they should be.

I'd treat #1 and #2 as blockers for opening signups next week. #3 and #4 should be fixed before real traffic arrives. When #1 is fixed, change the test to go through `app.handle` so it actually covers the real request path.