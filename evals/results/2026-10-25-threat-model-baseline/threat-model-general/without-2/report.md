I read all of `fixture/` and checked each finding below by running it against the real `app.handle` from a throwaway script outside the fixture. I didn't change anything. Every finding marked "Confirmed" reproduced.

## Critical: any customer can do these

**1. Negative quantities create unlimited store credit.** `orders.py:15-23`
The code never checks that `qty` is positive, so a negative quantity gives a negative total, and paying a negative total adds credit.
- Confirmed: bob (credit 5.00) ordered `{"sku":"gadget","qty":-1000}`. The total was −19990.00 and his credit went to **19995.00**.
- Mixing positive and negative lines gets goods almost free. `10 gadgets + −44 gizmos` charged bob **1.90 for ten gadgets**.
- `qty: 0` lines are also accepted.

**2. Anyone can export any customer's invoices.** `app.py:47` → `invoices.py:16`
`customer_id` comes straight from the request body. `export_csv` takes `user` but never checks it against `customer_id`.
- Confirmed: bob sent `{"customer_id": 1}` and got alice's invoice CSV.
- Customer IDs are small sequential integers, so it's trivial to walk every customer's purchase history.

**3. Signing up with different capitalization takes over or locks out an existing account.** `auth.py:35-39`
The "username taken" check uses the name exactly as typed, but the account is stored under the lowercased name.
- Signing up as `Alice` passes the check and **overwrites** `USERS["alice"]`.
- Confirmed: after signing up `Alice`/`pwned`, the real alice's password stops working, and logging in as `alice`/`pwned` succeeds as the new account.
- The original account is gone, along with its credit and its link to its invoices. Its existing tokens also stop working, because `user_by_id(1)` now returns nothing.
- The same works on staff. Confirmed: signing up `SAM` locked sam out. One request per name locks out every staff member, and nobody is left to issue refunds. The attacker doesn't get the staff role, though.

## Critical if the source ever leaks

**4. The token signing key is hard-coded in the source.** `settings.py:1`
Anyone with the source (a repo leak, a former contractor, a CI log) can make a valid token for any user ID, including staff.
- Confirmed: a token forged for uid 3 (sam) issued a refund.
- There's also no way to rotate the key or revoke tokens, short of a code change.

## High: anyone, no account needed

**5. Unhandled exceptions.** `handle` only catches `PermissionError`, `KeyError` and `ValueError`. Each of these raised an uncaught exception:
- A non-ASCII password at `/login` (e.g. `"é"`) → `TypeError` from `hmac.compare_digest` (`auth.py:45`). This needs no account.
- `GET /invoices` or `POST /refunds` with no ID → `IndexError` (`app.py:41,51`).
- A huge `qty` (`10**400`) → `OverflowError` (`orders.py:19`).
- Badly shaped bodies, like `items: ["x"]`, `qty: null`, or a body that's a list instead of an object → `TypeError` / `AttributeError`.

At best these are 500s. If your server handles a raised exception badly, anyone can crash or hang a worker. The traceback may also show internals.

**6. Mass signups can farm the 20.00 welcome credit.** `settings.py:3`, `auth.py:32`
Signup has no rate limit, no email or phone check, and no CAPTCHA. Each account is 20.00 of goods. Once signups open to the public, this is direct money loss even without bug #1.

**7. Login has no rate limit or lockout**, so password guessing has no cap. Any password length is accepted, including a single character (the test suite uses `"x"`).

## Medium

**8. Passwords are stored in plaintext.** `db.py:8`, `auth.py:45`
Once this moves to Postgres, a database leak exposes every customer's password, and people reuse passwords on other sites. Hash them with bcrypt, scrypt or argon2.

**9. Double-spend and double-refund race conditions.** `orders.py:21-23`, `orders.py:34-38`
Credit is checked and then deducted separately, and refunds check `amount > 0` before zeroing it, with no lock or transaction. With concurrent requests (several threads or workers, or Postgres "behind the same functions"), two orders can both pass the check against the same credit. Likewise, two refunds of the same invoice can both pay out.

**10. Usernames can be enumerated.** Signup says "username taken", and login returns faster for unknown users. Usernames also aren't validated: empty-after-trim, whitespace and lookalike Unicode names are all accepted. The Kelvin sign `K` lowercases to `k`, so it's another way into bug #3.

## Lower / design notes
- Money is stored as floats. It's rounded in places, but cents should be integers or `Decimal`.
- There's no logout or token revocation, and a stolen token works for the full hour.
- Invoice IDs are sequential. `get_invoice` checks ownership correctly, so this is only a problem combined with #2.

## Checked and fine
- `GET /catalog` and `/health` being public matches the README.
- `get_invoice` ownership checks work.
- The refund staff check works (given an honest token).
- Token signature comparison is constant-time.
- Expired tokens are rejected.
- No CSV injection: invoice lines only contain SKUs from the catalog.

**Fix before launch:** #1, #2 and #3 are each one request from any customer, and #3 needs no account. Then #4, #5 and #6.