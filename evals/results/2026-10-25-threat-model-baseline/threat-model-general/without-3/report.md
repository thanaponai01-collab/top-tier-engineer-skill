I ran each of the first five against `app.handle()` and they all work today. I wrote the test script outside `fixture/`, deleted it afterwards, and changed nothing in your code.

## Must fix before public signup

**1. Any customer can download any other customer's invoices.** `invoices.py:16` / `app.py:47`
`POST /invoices/export` takes `customer_id` from the request body and never checks it against the logged-in user. Bob sent `{"customer_id": 1}` and got Alice's full invoice CSV. User IDs are small sequential numbers, and signup even tells you yours, so one account can walk through every customer. The single-invoice endpoint does check ownership (`invoices.py:11`). Export doesn't.

**2. A negative quantity gives you free credit.** `orders.py:15-23`
`qty` is never checked to be positive. Bob ordered `{"sku":"gadget","qty":-1000}`: the total came to -19,990, it passed the "enough credit?" check, and his credit went from 5 to **19,995**. Negative lines can also be mixed with real ones: 50 gadgets plus -100 widgets cost him $0.50. A quantity of 0 is also accepted.

**3. Signing up with different capitalisation takes over an existing account.** `auth.py:35-39`
The "username taken" check uses the name exactly as typed, but the account is saved under the lowercased name. Signing up as `Alice` passes the check and replaces `alice`. After that, `alice` / attacker's password logs in, Alice's real password returns 401, her current session stops working, and her invoices become orphaned. Signing up as `SAM` did the same to the only staff account, leaving the shop with **no staff**, so no refunds and nobody who can see all invoices. The attacker doesn't inherit the victim's credit or role, but they get the username and the victim is locked out.

**4. Unlimited free money from new accounts.** `auth.py:37`, `settings.py:3`
Every signup gets $20 credit, and there's no rate limit, CAPTCHA, email check, or one-account-per-person rule. A script can create 1,000 accounts and spend $20,000. Even with #2 and #3 fixed, this is a business-logic hole.

**5. The token signing key is written in the source code.** `settings.py:1`
Anyone who sees the repo (a leak, an ex-contractor, a public fork) can make a valid token for any user ID. I forged one for user 3 (staff) and issued a refund with it. The key should come from the environment and be changed before launch, since it's already in the code.

## Serious, depending on how you deploy

**6. Seed accounts with known passwords.** `db.py:25-32`
If `db.reset()` seeding (it runs at import, `db.py:42`) reaches production, `sam` / `sam-pw` is a staff login, and the password is written in the tests.

**7. Passwords are stored in plain text, with no strength rule and no login throttling.** `db.py:8`, `auth.py:33`, `auth.py:43`
`"x"` is accepted as a password, and nothing slows down password guessing. If the database leaks, every password leaks with it.

**8. Simultaneous orders can spend the same credit twice** (`orders.py:21-23`). The credit check and the deduction are separate steps with no lock. That's harmless with the current in-memory store, but once it's "Postgres behind the same functions" as `db.py` plans, parallel orders can all pass the check.

## Lower severity

**9. Malformed requests cause unhandled crashes.** `handle()` only catches `PermissionError`, `KeyError`, and `ValueError`. These all raised other exceptions:
- `GET /invoices` with no ID → `IndexError`
- `items: ["x"]` → `TypeError`
- `qty: 10**400` → `OverflowError`
- a JSON array as the body → `AttributeError`
- a non-string username → `AttributeError`

What happens next depends on your web server: a 500, a stack trace shown to the user, or a crashed worker. A refund on an invoice whose owner was replaced (see #3) would also crash at `orders.py:37`.

**10. The error code reveals which invoice IDs exist.** You get 403 if an invoice exists but isn't yours and 400 if it doesn't exist, so anyone logged in can map the invoice numbers.

**11. Sessions can't be ended.** There's no logout or revocation, so a stolen token works for the full hour. A forged token from #5 also works for as long as the key is unchanged.

One thing the tests don't catch: they only check the paths that are supposed to work (plus the "other customer's invoice" and "refund is staff-only" cases). None of #1–#4 has a test, so they all pass with these holes open.

Items 1–3 are each one-request exploits that anyone with a free account can do, and #4 needs no special skill at all. I'd fix those four and rotate the key (#5) before next week.