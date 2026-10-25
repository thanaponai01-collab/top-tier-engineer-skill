There's one serious hole that should block the public launch: **any logged-in customer can issue refunds**, which in practice gives them unlimited free goods. All 8 tests pass anyway, because the test that's supposed to catch this is looking in the wrong place. I confirmed the main findings by running them against the code. I haven't changed anything.

## Critical: the staff-only check on refunds never runs for real requests

`app.py:84-85` puts the staff check on refunds by replacing the module-level name `r_refund` with a guarded version. But that happens *after* `ROUTES` (`app.py:57-66`) was built, and `ROUTES` already holds the original, unguarded function. `handle()` only ever looks up `ROUTES`, so the guard does nothing for actual requests.

- `ROUTES[("POST","refunds")] is app.r_refund` comes back `False`.
- Bob, a customer, called `POST /refunds/100` on Alice's invoice and got `200`. Alice's credit went from 50.0 to 92.5.
- **Free goods for any new signup:** I signed up as `eve` (20.00 welcome credit), ordered a gadget for 19.99, refunded it, and got the full credit back. I repeated it three times and the credit was 20.00 every time, while the orders kept going through.
- **Why the tests don't catch it:** `test_refund_staff_only` calls `app.r_refund(...)` directly, which is the guarded name. It never goes through `app.handle`, which is the path real requests take.

The "wrapped in one place so a new staff route can't forget its check" pattern is fragile by design: it silently does nothing if the dispatch table captured the function first. `orders.refund` itself takes a `user` argument and never checks it, so there's no second line of defence either.

## Medium

- **Free credit from fake accounts.** Every signup gets 20.00 credit (`settings.py:6`, `auth.py:37`). There's no verification, rate limit or captcha, so anyone can script signups and spend 20.00 per account. Once signups are public, that's real money.
- **Bad input causes unhandled errors (500s and possibly stack traces).** `handle()` only catches `PermissionError`, `KeyError` and `ValueError`. Three cases I confirmed crash with an uncaught exception:
  - `POST /refunds` with no ID → `IndexError` (`GET /invoices` with no ID does the same).
  - Login (or signup) with a non-string username, e.g. `{"username": 1}` → `AttributeError`. A non-string password at login gives a `TypeError`.
  - An order item like `{"sku": ["x"], "qty": 1}` → `TypeError`. Items that aren't objects, or are missing keys, also fail in ways that aren't handled cleanly.

  How bad this is depends on what the web server does with an exception: whether it shows tracebacks and whether the worker stays up. None of these requests need a login.
- **Race conditions once the server handles requests concurrently.** I reasoned these from the code rather than reproducing them:
  - `place_order` checks the credit and then deducts it as separate steps (`orders.py:23-25`). Parallel orders can spend the same credit twice.
  - `signup` checks the username, then assigns `max(id)+1` (`auth.py:35-39`). Two signups at the same moment can end up with the same user ID. `user_by_id` returns the first match, so one person's token could log them into the other's account, or a signup could overwrite another.
  - `refund`'s once-only check (`orders.py:34-38`) has the same race.
- **Passwords are stored in plain text** (`db.py:8`, compared at `auth.py:45`). Any database leak or log dump exposes every customer's password, and with it their accounts on other sites.
- **Unlimited password guessing.** Login has no rate limiting or lockout, and signup accepts a 1-character password.

## Low / worth knowing

- **Sessions can't be ended early.** Tokens are signed but there's no way to revoke them: no logout and no password change. A stolen token works for the full hour.
- **Restarts and multiple workers break logins.** If `SHOP_SECRET` isn't set, the signing key is random per process (`settings.py:4`). Everyone is logged out on each restart, and with several workers, tokens fail at random. Set the variable in production.
- **Lookalike usernames are allowed.** Names are lowercased but not trimmed or normalised, so `"alice "` and other near-copies of `alice` can be registered.
- **Invoice IDs leak a little.** They're sequential, and a missing invoice gives `400` while someone else's gives `403`, so anyone can tell which IDs exist and roughly how many orders the shop gets. Contents stay protected: `get_invoice` checks the owner correctly.
- **Slow login failures give away usernames.** Login fails faster when the username doesn't exist, which makes it possible to tell which usernames are registered.
- **Large requests can tie up the server.** There's no limit on how many lines an order can have.

## What looked fine

- **Viewing and exporting invoices:** both are limited to the caller's own invoices. Export always uses the caller's ID.
- **Prices and quantities:** prices come from the server, and quantities are limited to 1–100, so there are no negative-price or negative-quantity tricks.
- **Token signing:** it uses HMAC and a constant-time comparison.
- **The public catalog:** it's public by design, as the README says.

To fix the critical one, apply the staff check inside `ROUTES` itself (or inside `orders.refund`). Then change the test so it goes through `app.handle("POST", "/refunds/101", ...)` and checks that a customer gets a `403`.