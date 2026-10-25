I ran the threat model over all 9 ways into the app. Right now, any logged-in customer can issue refunds. That is staff-only by design, and it was supposed to be closed off last month. I haven't changed any code. I added the attacks as tests in `fixture/tests/test_threats.py`: 5 of them fail today because the attack works, and 5 pass because it's blocked.

## What works today, worst first

**1. Any customer can refund any invoice: `POST /refunds/<id>`** (`app.py::r_refund`)
- **Cause:** the staff check doesn't apply to web requests. `ROUTES` (`app.py:57`) stores the original `r_refund` function when the module loads. The `permissions.protect(...)` call at `app.py:85` runs afterwards and only replaces the module's `r_refund` name; the dict still points at the unprotected original. `app.handle` looks routes up in that dict, so the staff check never runs over HTTP.
- **Why tests missed it:** the existing `test_refund_staff_only` passes because it calls `app.r_refund` directly, which is the protected version. It never goes through `handle`.
- **What an attacker gets:**
  - *Free goods:* they order, refund their own invoice, and keep the goods plus all their credit. Your existing test bob does it: credit goes 5.00 → 0.50 → 5.00.
  - *Anyone's invoice:* they can refund other customers' invoices too. Bob refunding invoice 100 pushed alice's credit to 92.50.
- **Fix:** put the check where the route is used. Either protect the handlers before `ROUTES` is built, or have `ROUTES` call through the module name. `orders.refund` should also refuse non-staff callers itself, as a second guard.
- **Tests:** `test_customer_cannot_refund_through_http`, `test_customer_cannot_refund_own_order_for_free_goods`.

**2. Unlimited signups each come with 20.00 of credit you can spend** (`app.py::r_signup`)
- Signup is public, needs nothing but a username, and every account gets `SIGNUP_CREDIT` (`settings.py:6`). Ten throwaway accounts took 199.80 of widgets.
- Once signups open, this is money out the door. How to limit it is your call, e.g. verified email or payment method before welcome credit can be spent, or one welcome credit per verified person.
- **Test:** `test_throwaway_signups_cannot_farm_welcome_credit`. It passes once 10 throwaway accounts can take less than half of that.

**3. Malformed requests crash the handler instead of getting a 400** (`app.py::r_invoice`, `app.py::r_order`)
- **No invoice id:** `GET /invoices` raises `IndexError` on `args[0]`.
- **Bad items:** `"items": {...}` sent as an object instead of a list, or a non-string `sku`, raises `TypeError`.
- `handle` only catches `PermissionError`, `KeyError` and `ValueError`, so these reach the web server as unhandled exceptions. No data is exposed. It's noisy 500s, and possibly stack traces, depending on the server.
- **Fix:** check the shape of the input in the handlers.
- **Tests:** `test_invoice_without_id_is_refused_not_crash`, `test_malformed_order_is_refused_not_crash`.

## Attacks that were blocked
- **Signup:** signing up as `ALICE` to take over alice's account is refused, and a `role: staff` sent in the signup body is ignored.
- **Login and tokens:** forged tokens, expired tokens and an empty password are rejected.
- **Invoices:** reading another customer's invoice gets a 403.
- **Export:** pointing it at another customer with `customer_id` in the body is ignored; you only get your own.
- **Orders:** quantities like `-1`, `0`, `101`, `"-5"` and `False` can't get goods past the credit check.

No attack was run on three of them, because there's nothing behind them to gain:
- `/health` returns a constant.
- `/catalog` is the public price list, public by design.
- The `__main__` block only runs locally and takes no input.

## Not covered
- **Two orders at once:** `place_order` checks credit and then deducts it as separate steps. On a multi-threaded server, two simultaneous orders could both pass the check. I read this in the code but didn't attack it.
- **Plaintext passwords:** passwords are stored and compared in plain text (`db.py`, `auth.py:45`). Nothing exposes them today, but a database leak would.
- **Signing key:** if `SHOP_SECRET` isn't set, `SECRET_KEY` is random per process. Logins die on every restart and don't carry across multiple workers. That's an operations problem rather than a hole.
- **Not tested:** the web server in front of the app, the real database that would replace `db.py`, and dependencies. No secrets are hardcoded in the source.

The new tests will turn red if a later change reopens any of these. The `.threat/` folder is the tool's working notes; delete it, or commit it with the fixes when you get to them.

<!-- file written by the agent: fixture/.threat/doors.md -->
# Doors

One line per way in that no attack entered: `- DOOR: out: <why>`. A door an attack entered needs no line.

- app.py::__main__: out: only runs when an operator executes app.py locally; it takes no input and prints the public price list
- app.py::r_catalog: out: returns a copy of the static public price list (public by design per README); takes no input, writes nothing
- app.py::r_health: out: returns the constant "ok"; reads no input and touches no data
