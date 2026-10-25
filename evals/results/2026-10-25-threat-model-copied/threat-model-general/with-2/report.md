The worst thing today, **proven**: any customer can give themselves unlimited store credit with one order that has a negative quantity. Bob started with $5.00, ordered 1 gadget plus −100 widgets, and ended with $984.01. A second problem is just as serious: the token-signing key is hardcoded in source, so anyone who can read the code can make a staff token without a password.

I ran every "proven" attack below against the in-memory fixture with its seeded fake users. The attack script is in a separate directory (`%TEMP%\tm-scratch\attacks.py`), so `fixture/` is untouched. I changed nothing, and the existing 8 tests still pass. None of those tests tries any of these attacks.

## Findings, worst first

| # | Boundary | What the attacker gets | Evidence | Fix direction |
|---|---|---|---|---|
| 1 | client → `POST /orders` (`orders.py:15`) | **Unlimited money.** `qty` comes from the client and is never checked for ≥ 1, so a negative line makes the total negative and `credit - total` adds to the balance. | **proven**: total −979.01, bob's credit 5.00 → 984.01 | Reject `qty < 1` and set an upper limit. |
| 2 | Secret in source (`settings.py:1`, `SECRET_KEY`) | **Staff access.** Anyone with the source can sign a token for uid 3 (staff), then read every invoice and refund any invoice. | **proven**: a forged token read invoice 101 and refunded invoice 100 | Load the key from the environment or a secrets store, and **rotate it**: treat the current value as burned, since it's in source and any copies or history. |
| 3 | client → `POST /invoices/export` (`app.py:47`, `invoices.py:16`) | **Every customer's invoice history.** `customer_id` comes from the request body, and `export_csv` never checks who owns it. `GET /invoices/<id>` does check ownership (`invoices.py:11`), so the two surfaces apply different rules to the same data. | **proven**: alice exported bob's invoice 101 | Apply the same owner-or-staff check as `get_invoice`. Better, ignore `customer_id` for non-staff. |
| 4 | `POST /signup` (`auth.py:35` vs `:39`) | **Account overwrite.** The "taken" check uses the raw name, but the account is stored under the lowercased name. Signing up as `Sam` replaces the real staff account `sam`: the real password stops working and the attacker logs in as `sam`. Signing up as `ALICE` kills alice's live sessions and leaves her invoices with no owner. | **proven**: real sam's login → 401, attacker's login as `sam` → 200, new role `customer`. Alice's existing token → 403 | Normalise the username once, then check and store that same key. Consider Unicode normalisation (NFKC + casefold) too. |
| 5 | Public signup + `SIGNUP_CREDIT` | **Free goods at scale.** Each signup gets $20 credit, and nothing limits how many accounts one person can create. | **proven**: 50 scripted signups → $1,000 of credit | This is a business decision: limit signups, or only release credit after a verification step or a first purchase. |
| 6 | Malformed input → `handle` (`app.py:71-76`) | **Crashes (unhandled exceptions).** `handle` only catches `PermissionError`, `KeyError` and `ValueError`, so other bad input escapes as a 500 or a crashed worker. This hits anyone who can send a request, and some cases need no login at all. | **proven**: `qty: 10**400` → `OverflowError`; `items: ["widget"]` → `TypeError`; `GET /invoices` with no id → `IndexError`; a non-string password on unauthenticated `/login` → `TypeError` | Validate the types and shape of the request body. Add a catch-all that returns 400 or 500 without leaking details. |
| 7 | Concurrency in `refund`, `place_order`, `signup` | **Double refund, overspent credit, duplicate user ids.** Each of these reads a value, checks it, then writes, with no lock or transaction in between. In-memory this is single-threaded; on the Postgres deployment the README mentions, two requests at once could both pass the check. | **suspected**: not runnable without a concurrent server | Use a conditional `UPDATE … WHERE amount > 0` or row locks, and let the database generate ids. Settle it by firing 20 identical refund or order requests at once and asserting exactly one succeeds. |
| 8 | Stored credentials (`db.py:8`) | **Every password at once if the database leaks.** Passwords are stored in plaintext. | **traced** | Hash passwords with argon2, bcrypt or scrypt. |
| 9 | Sessions (`auth.py`) | **Sessions that can't be killed.** There's no logout or revocation, and changing a password won't end a stolen session within its one-hour lifetime. There's also no rate limit on `/login`, so passwords can be guessed indefinitely. | **traced** | Add a per-user token version or deny-list, and rate-limit login. |

**Held (tried, defense worked):**
* A customer can't fetch someone else's invoice through `GET /invoices/<id>`.
* A non-staff user can't call `/refunds`.
* A tampered token signature is rejected (constant-time compare).
* Expired tokens are rejected.
* Unknown SKUs are rejected.
* The same invoice can't be refunded twice in a row.
* Export CSV injection isn't possible, because SKUs only come from the catalog.
* `/catalog` and `/health` being public is by design (README), so it isn't counted as a finding.

## Abuse-case test specs (each must pass once fixed)

1. bob orders `[{gadget,1},{widget,-100}]` → 400. Bob's credit stays 5.00 and no invoice is created. Same for `qty: 0`.
2. A token signed with the *old* key → 403 after rotation. Also check that a token for uid 3 can't be made without the runtime key.
3. alice exports with `{"customer_id": 2}` → 403, or only her own rows. Bob's `101,` row is never in her output. Alice's own export still contains `100,42.50`, and staff can still export any customer.
4. Signup `Sam` → 400 "username taken". `sam`/`sam-pw` can still log in with role `staff`. Same for `ALICE`, and alice's existing token keeps working.
5. Signup is limited per source, or new-account credit can't be spent until the account is verified (exact behaviour depends on what you decide).
6. `qty: 10**400`, `items: ["widget"]`, `GET /invoices`, and `password: 123` each return a 4xx, never an unhandled exception.
7. 20 concurrent `POST /refunds/100` as sam → exactly one 200, and alice's credit goes up by 42.50 once.

## Assets (ranked by worst case)

| Asset | Who wants it | Worst case |
|---|---|---|
| Store credit / money | any customer | unlimited goods (#1, #5, #7) |
| Staff privilege | anyone | read every invoice and refund at will (#2, #4) |
| Customer invoice data | other customers, competitors | full purchase history of every customer (#3) |
| Accounts and sessions | anyone | lock out or hijack a username, including staff (#4, #8, #9) |
| Availability | anyone | crash a worker with one request (#6) |

I modelled 6 boundaries: unauthenticated network → app, token → identity, customer → staff, client body → order pricing, client body → export scope, and concurrency. Only token → identity held, and only for tampered or expired tokens; the leaked key breaks it. All the others have at least one proven break, except concurrency, which is suspected.

Some fixes change who is trusted (where the signing key lives, how usernames are normalised, export scope for staff vs customers) or are business calls (signup credit). Say which you want first and I'll turn these specs into failing tests before fixing.