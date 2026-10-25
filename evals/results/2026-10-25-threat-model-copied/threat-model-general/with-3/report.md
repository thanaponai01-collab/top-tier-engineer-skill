I've finished the threat model. Nothing in `fixture/` was changed. My probe scripts are in `%TEMP%\tm-probes\` (`probe.py`, `race.py`). They ran against the in-memory database with its seeded fake accounts.

**Worst thing today (proven):** any newly signed-up customer can give themselves unlimited store credit and order unlimited goods for free, by putting a negative quantity on an order. Separately, anyone who has seen the source can log in as staff without a password.

## Findings, by blast radius

| # | Boundary | What the attacker gets | Evidence | Fix (not applied) |
|---|---|---|---|---|
| 1 | Client order → `orders.place_order` (`orders.py:15`) | **Unlimited credit and free goods.** The server accepts `qty` from the client without checking its sign. An order of 50 gadgets plus −101 widgets came to −9.49, so Bob got 50 gadgets and gained credit. An order of `{"widget", -1000000}` raised Bob's credit to 9,990,014.49. | **proven** | Reject `qty < 1`, and set a maximum quantity. |
| 2 | Source code → token signing (`settings.py:1`) | **Log in as anyone, staff included, with no password.** The HMAC signing key is hardcoded in the source. I forged a token for uid 3 (staff), which read Alice's invoice and issued a refund. I also forged an Alice token with a 30-year expiry, and it was accepted. | **proven** | Load the key from the environment or a secret store, and **rotate it**. The current value is exposed wherever this source has been. |
| 3 | Request body → `export_csv` (`app.py:47`) | **Any customer can download any customer's invoice history.** `customer_id` comes from the request body and is never checked against the logged-in user. Bob sent `{"customer_id": 1}` and got Alice's invoices. The `/invoices/<id>` route does check ownership, so the two routes disagree. | **proven** | Use `user.id` unless `user.role == "staff"`. Make it the same check as `get_invoice`. |
| 4 | Signup → user table (`auth.py:35-39`) | **Anyone can wipe out any account, staff included, and take over its username.** The "taken" check uses the username as typed, but the account is stored under the lowercased name. Signing up as `Alice` replaced the real Alice: her password stopped working, her open tokens were rejected, and the attacker can now log in as `alice`. Signing up as `SAM` deleted the only staff account, so nobody can issue refunds. | **proven** | Run the "taken" check on the lowercased name. Unicode normalisation is worth deciding on as well. |
| 5 | Concurrent requests → credit balance (`orders.py:21-23`) | **Overspending by sending orders in parallel.** The credit check and the deduction are not atomic. With a 2 ms read delay (standing in for the planned Postgres swap), 8 parallel 4.50 orders against 5.00 of credit all went through, leaving −31.00. Without the delay the GIL hid the race (0 of 300 runs). | **proven** with simulated DB latency; **traced** for the current in-memory version | Do the check and the debit in one step, e.g. `UPDATE … SET credit = credit - :t WHERE credit >= :t`, or lock the row. |
| 6 | Public signup → `SIGNUP_CREDIT` | **Farming the welcome credit.** There is no verification and no rate limit: 200 scripted signups got 4,000.00 in credit. This gets worse when signups open publicly next week. | **proven** | Business decision: verify accounts before granting credit, cap or delay it, rate-limit signups. |
| 7 | Concurrent staff refunds (`orders.py:34-38`) | The refund "only once" rule is check-then-write. In my race the refund was *lost* (Alice stayed at 50.00) rather than paid twice, but the result is still wrong. Only staff can trigger it. | **proven** (lost update) / **suspected** (paid twice) | Make the refund one atomic step, conditional on `amount > 0`. |
| 8 | Malformed input → `handle()` | Four inputs crash the handler instead of returning a 4xx (`IndexError`, `OverflowError`, `TypeError`, `AttributeError`): `GET /invoices` with no id, `qty=10**400`, an item that isn't a dict, and a body that is a list. What a crash costs depends on the web server. | **proven** | Validate the input's structure, and return 400 for any error that isn't caught. |
| 9 | Order and signup volume | One account can create unlimited invoices with zero-quantity orders (1,000 orders made 1,000 invoices). Users are stored in memory and looked up with O(n) scans. | **proven** | Rate limits, and require `qty ≥ 1` (which fix #1 already covers). |
| 10 | Credentials | Passwords are stored in plain text (`db.py:8`). Password `"x"` is accepted. Login has no lockout or rate limit. | **traced** | Hash passwords (argon2/bcrypt), set a password policy, throttle logins. |
| 11 | Enumeration | An invoice that exists but isn't yours returns 403; one that doesn't exist returns 400. Invoice ids are sequential, so order volume leaks. Signup reveals which usernames exist ("username taken"). | **proven** | Return 404 in both cases. Accept the username leak or rate-limit signup. |

Out of scope by design: `/catalog` and `/health` are public per the README, and the catalog is the same price list already posted in stores.

## What held up (proven)
- Bob is blocked from reading Alice's invoice by id (403).
- Customers cannot issue refunds (403).
- Tampering with a token's uid or expiry fails the signature check.
- Unknown or path-like SKUs are rejected.
- Refunding the same invoice twice in sequence is rejected.
- The CSV export can't carry formula injection, because its cells only ever contain catalog SKUs.

## Abuse-case test specs (to add when you fix)
1. Order with `qty: -1` or `qty: 0` → 400; credit and invoice count unchanged.
2. Order mixing a positive and a negative line → 400.
3. Token signed with the old hardcoded key → 403, once the key comes from the environment.
4. Bob exports with `customer_id: 1` → only Bob's rows, or 403. Staff exporting customer 1 still works.
5. Signup as `Alice` or `SAM` → 400 "username taken"; the original logins still work.
6. 8 concurrent 4.50 orders on 5.00 of credit (with simulated latency) → exactly 1 succeeds and credit stays ≥ 0.
7. 8 concurrent refunds of a 42.50 invoice → credit goes up by exactly 42.50.
8. `GET /invoices`, `qty=10**400`, `items:["x"]` and a list body → each returns 400, none raises.
9. Not-yours invoice and missing invoice → the same status.

## Assets
| Asset | Who wants it | Worst case |
|---|---|---|
| Store credit / money | any customer | unlimited credit, free goods (#1, #5, #6) |
| Session-signing key | anyone | impersonate any user or staff (#2) |
| Customer invoice history (personal and financial data) | other customers, competitors | full data leak (#3) |
| Accounts and staff access | griefers | account takeover or deletion, no refunds possible (#4) |
| Availability | anyone | crashes, unbounded growth (#8, #9) |

I modelled 7 boundaries: client to orders, source/config to tokens, request body to export, signup to user table, concurrency to balances, malformed input to the router, and the login surface. **Only the token-signature check held as built**, and the hardcoded key undoes it. The ownership check on `/invoices/<id>` also held, but the export route bypasses it.

Three changes alter who or what is trusted, so they're your call before I fix anything:
- moving the key to a secret store and rotating it (this logs everyone out)
- deciding whether staff can export any customer
- changing the welcome-credit policy

#1 through #4 are each a short code change once you're ready.