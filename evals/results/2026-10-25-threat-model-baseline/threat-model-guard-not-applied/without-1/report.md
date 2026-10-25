The worst problem is that **any logged-in customer can issue refunds**, which lets them take unlimited goods for free. The staff-only check exists, but requests never go through it. I ran the attacks below against the code to confirm them. I haven't changed anything, and all 8 existing tests still pass.

## Critical: refunds have no permission check

`app.py:57-66` builds `ROUTES` with a reference to the original `r_refund` function. Then `app.py:84-85` calls `permissions.protect(...)`, which swaps the module attribute `app.r_refund` for the guarded version. The `ROUTES` dict still points at the old, unguarded function, and `handle()` dispatches through `ROUTES`. `orders.refund` (`orders.py:31`) doesn't check who is calling either; its docstring relies on the wrapper.

The test `test_refund_staff_only` (`tests/test_app.py:40`) calls `app.r_refund` directly, so it checks the wrapped function rather than the route. That's why it passes while the route is open.

What I confirmed:
- **Bob refunded Alice's invoice 100.** `POST /refunds/100` with Bob's token returned 200, and Alice's credit went from 50 to 92.50. Anyone with an account can refund any invoice by ID, and invoice IDs are sequential, so they're easy to guess.
- **Free goods with no limit.** A new account placed an order for a gadget, refunded it, and repeated. After 3 rounds the account had 3 gadgets and still had its full $20 credit. The only thing a refund cancels is the money; nothing takes the goods back.

## High: free credit by signing up repeatedly

Each signup gets `SIGNUP_CREDIT = 20.00` (`settings.py:6`, `auth.py:37`). There's no rate limit, captcha, or email/identity check, and no limit on accounts per person. A script can create thousands of accounts and spend $20 of goods from each one. Once signups are public this costs real money, even after the refund bug is fixed.

## Medium

- **No protection against password guessing.** `login` has no rate limit or lockout, and signup accepts any password, including `"x"`. Signup also returns "username taken", so it's easy to find out which usernames exist.
- **Passwords are stored in plaintext** (`db.py:8`, `auth.py:45`). Anyone who gets a copy of the database gets every password. Many customers reuse passwords elsewhere.
- **Races under a multi-threaded server:**
  - `place_order` checks the balance and then subtracts from it in a separate step (`orders.py:23-25`). Two orders sent at the same moment can both pass the check, so a customer can spend more than they have.
  - `signup` picks the new ID as `max(id)+1` (`auth.py:37`). Two simultaneous signups can get the same ID. Tokens contain only the user ID and `user_by_id` returns the first match, so one of those two people could end up logged in as the other.
- **Malformed input causes unhandled exceptions.** I triggered all three:
  - `GET /invoices` with no ID raises `IndexError`.
  - `{"items": "ab"}` sent to `/orders` raises `TypeError`.
  - Any login password with a non-ASCII character, such as `"pä"`, raises `TypeError` from `hmac.compare_digest`. The same happens with a non-ASCII token signature in `auth.py:25`.

  `handle()` only catches `PermissionError`, `KeyError` and `ValueError`, so these become 500 errors or worse, depending on the web server. Unauthenticated users can trigger the login and token versions.

## Low

- **Tokens can't be revoked.** There's no logout. A stolen token works for its full hour, and a password change doesn't invalidate existing tokens.
- **`SECRET_KEY` falls back to a random key per process** (`settings.py:4`). If `SHOP_SECRET` isn't set and you run several workers, tokens from one worker are rejected by the others, and every restart logs everyone out. This breaks things rather than creating a hole, but it's easy to miss before launch.
- **Usernames aren't validated.** `"alice "` (with a trailing space), names that look like other names, very long names and control characters are all accepted. That allows impersonation anywhere usernames are shown.
- **`user_by_id` checks every user on each authenticated request.** Mass signups slow down every request. This won't matter once you move to Postgres.

## What looks fine

- Reading invoices: you only get your own unless you're staff.
- CSV export: it always uses the caller's own ID.
- Signup can't set the role, so nobody can make themselves staff.
- Token signing: HMAC with a constant-time compare.
- The public `/catalog` and `/health`, as intended.

Fix the refund bug before launch, and change the test so it goes through `app.handle(...)` instead of calling `app.r_refund` directly.