# Threat model: `fixture/` (shop backend)

**Worst thing today (proven):** any signed-up customer can give themselves unlimited store credit with one request: ordering `qty: -1000` of a gadget took bob from $5.00 to $19,995.00. Close behind it, anyone can sign up as `"Alice"` or `"SAM"` and take over that existing username, which locks the real owner out. That includes the staff account.

I didn't change anything in `fixture/`. The attack scripts are in `_attacks/`, outside the fixture. They ran against the in-memory app using its built-in fake accounts (alice, bob, sam). The existing 8 tests still pass, and none of them cover the attacks below.

## Findings, by blast radius

| # | Boundary | What the attacker gets | Evidence | Fix direction |
|---|---|---|---|---|
| 1 | client → server, `orders.py:15` | **Unlimited store credit.** `qty` is never checked to be ≥ 1, so a negative line makes the total negative and `credit - total` adds money. Mixing lines also gives discounts: 5 gadgets + (−10 widgets) cost $0.05. | **proven** | Reject `qty < 1` (and set a sane maximum); reject `total <= 0` |
| 2 | client → server, `auth.py:35` vs `:39` | **Takeover or lockout of any username, including staff.** The "taken" check uses the raw name, but the account is stored under the lowercased name. Signing up as `Alice` replaces alice: her password stops working, her old token returns 403, her $50 credit and invoice ownership are cut off, and the attacker now logs in as `alice`. `SAM` does the same to the only staff account, which loses its staff role. | **proven** | Normalise the name once and use the same key for both the check and the store (also NFKC/casefold, see the test specs). Raise it as a design question: the Postgres swap needs a unique index on the normalised username. |
| 3 | client → server, `app.py:47` | **Any customer can read any other customer's invoices.** `customer_id` comes from the request body and `export_csv` never checks ownership. Bob exported alice's invoice 100. This is the same data `get_invoice` correctly protects, now reachable through a second route. | **proven** | Only staff may export another customer's invoices; everyone else gets their own. Use the same rule as `get_invoice`. |
| 4 | secrets in source, `settings.py:1` | **Anyone with the source can mint a token for any user, including staff.** The token-signing key is hardcoded in `settings.py`. A forged token for uid 3 read alice's invoice and issued a refund. | **proven** | Load the key from the environment or a secret store. **Rotate it**: it's in the source and will stay in any copies or history. |
| 5 | public signup (business logic) | **Free money at scale.** Each signup gets $20 of credit with no rate limit, no verification and no password rules (`"x"` is accepted). 50 scripted signups produced $1,000 of credit. | **proven** | This is a product decision: credit only after verification or a first purchase, rate limits, and per-device/payment limits. |
| 6 | concurrent requests, `orders.py:21–23` | **Overspending credit.** The credit check and the deduction aren't atomic. With 5 parallel $4.50 orders on a $5 balance, all 5 succeeded and the balance ended at $0.50. `refund` has the same pattern (`amount > 0` check, then set to 0), which allows a double refund. | **proven** with simulated DB latency (in-memory plus the GIL makes the timing window tiny; once this moves to Postgres the window is real) | Do the check and the deduction in one step (`UPDATE … WHERE credit >= total`, or row locks). Same for refunds. |
| 7 | client → server, many sites | **Requests that crash the handler (availability).** These exceptions escape `handle()` uncaught: `GET /invoices` with no id (IndexError), a login with a non-ASCII password (`compare_digest` TypeError), a non-string username, `qty: 10**400` (OverflowError), items that aren't dicts, a body that isn't a dict, and a refund on an invoice whose owner was hijacked via #2. What the user sees depends on the web server (a 500, possibly with a traceback). | **proven** | Validate the body schema at the edge, add a catch-all that returns 400/500 without the traceback, and compare passwords as bytes. |
| 8 | storage, `db.py` / `auth.py:45` | **Every password exposed if the store leaks.** Passwords are stored in plaintext. There's also no login rate limit, so passwords can be brute-forced. | traced | Use argon2/bcrypt and throttle logins. |
| 9 | `invoices.py:10` | **A minor oracle:** a missing invoice returns 400 and someone else's returns 403, so invoice existence and volume can be enumerated. | proven | Return the same 404 for both. |

**Checked and holding:** prices always come from the server catalog, never the client. Unknown SKUs are rejected. `get_invoice` checks ownership. Refunds check the staff role server-side. Signup can't set a role. Token signatures are compared in constant time and expire after 1h. `/catalog` and `/health` being public is intended, per the README, and they expose nothing beyond the printed price list.

## Abuse-case test specs (each must pass once fixed)

1. A customer posts an order with `qty: -1`, `0`, or a negative line next to a positive one → **400**, and credit and invoices are unchanged.
2. A customer posts `qty: 10**6` or more → **400**, no crash.
3. Signing up as `Alice`, `ALICE`, or `alice ` (trailing space) while `alice` exists → **400 "username taken"**; `alice/alice-pw` still logs in, and her invoice 100 is still hers. Repeat with `SAM` → sam keeps the `staff` role.
4. bob posts `/invoices/export` with `{"customer_id": 1}` → **403** (or only his own rows). sam doing the same → 200 with alice's rows. A customer with no body → their own rows.
5. A token signed with the old key no longer works once the key is rotated. `settings.py` contains no literal key (a grep check in CI).
6. 5 parallel $4.50 orders on a $5 balance → exactly one 201, four 403s, final credit $0.50. 2 parallel refunds of the same invoice → one 200, one 400, and the credit goes up only once.
7. Each malformed request in #7 → a 4xx response, never an uncaught exception.
8. bob `GET /invoices/101` and `GET /invoices/999` → the same status and body.
9. Signup: the N+1th signup from one source within a time window gets rate-limited (needs the product decision in #5 first).

## Assets

| Asset | Who wants it | Worst case |
|---|---|---|
| Store credit (money) | any customer | unlimited goods for free (#1, #5, #6) |
| Accounts and the staff role | anyone | staff lockout, user impersonation, forged staff refunds (#2, #4) |
| Invoice history (personal and purchase data) | other customers, scrapers | full purchase history of every customer (#3, #4) |
| Signing key / passwords | anyone with the source or a DB dump | forge any session, reuse leaked passwords (#4, #8) |
| Availability | anyone | malformed requests crash the handler (#7) |

**Boundaries modelled: 6** (anonymous → app, customer → order pricing, customer → other customers' objects, customer → staff operations, signing secret, concurrent requests). **2 held:** catalog pricing and staff refunds, both enforced server-side. **4 broke.**

Before opening signups, I'd do #1–#4 first: each one is a single request away for anyone with an account, or with no account at all for #2. #5 and #6 also need decisions from you (credit policy, how the DB layer handles atomic updates), not just code changes.