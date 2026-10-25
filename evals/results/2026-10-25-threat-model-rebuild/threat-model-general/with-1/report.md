I ran the threat model over `fixture/` and fixed nothing. Seven abuses work today and two defenses held. The helper's check passed: all 9 ways into the app were attacked or shown to expose nothing.

## Open today, worst first

1. **Anyone with the source can sign in as any user, including staff.** The token signing key is written directly in `settings.py:1`. With it, a forged token for uid 3 (sam, staff) reads any invoice and can issue refunds. This matters if the repo leaks or an ex-employee has a copy. I've only given its location here, not the value. **Fix:** load the key from the environment or a secret store, and **rotate it**: treat the current value as compromised.
2. **Anyone, without logging in, can take over an existing account's username.** `auth.signup` checks whether the username exists exactly as typed, but saves it lowercased (`auth.py:35` vs `:39`). Signing up as `Sam` overwrites the staff account: the real sam can no longer log in, and the attacker's password now works for "sam". **Fix:** in `auth.signup`, check `username.lower()` before saving.
3. **Any customer can give themselves unlimited store credit.** Ordering `{"sku": "widget", "qty": -100}` gives a total of −999. That passes the credit check and *adds* 999 to their balance (`orders.py:15-23`). Mixing negative and positive lines also gets goods free. **Fix:** in `orders.place_order`, reject `qty < 1` and set an upper limit.
4. **Any customer can export another customer's full invoice history.** `POST /invoices/export` with `{"customer_id": 2}` returns bob's invoices to alice. `export_csv` never checks who is asking (`invoices.py:16`, `app.py:47`). **Fix:** in `invoices.export_csv`, apply the same owner-or-staff check that `get_invoice` uses.
5. **Malformed input crashes the app with uncaught exceptions (500s):**
   - A non-ASCII character in the bearer token crashes every logged-in route (`auth.py:25`; `hmac.compare_digest` rejects non-ASCII strings).
   - A non-ASCII password crashes `/login` (`auth.py:45`).
   - `qty: 10**400` crashes `/orders` with an `OverflowError`.

   **Fix:** compare encoded bytes in `auth`, and put a limit on `qty`.

## Held (attacked, refused)
- A customer reading another customer's invoice through `/invoices/<id>` gets 403.
- A customer issuing a refund gets refused, and staff can't refund the same invoice twice.

## Shown to expose nothing
`/health` (constant reply), `/catalog` (public by design, per the README, and changes nothing) and the `__main__` block (runs only by hand, with a fixed call).

## Not covered
These I only read about, or didn't attack:
- **Signup credit farming:** every new account gets 20.00 credit and nothing limits signups. That's free goods at scale once you open to the public. It's a policy decision rather than a code bug.
- **Login:** there's no rate limit, so passwords can be guessed by brute force.
- **Passwords** are stored in plaintext in `db.User`.
- **Tokens** can't be revoked before they expire.
- **Concurrency:** credit updates aren't atomic, so simultaneous requests could double-spend.
- **Other bad request bodies**, like `items` that isn't a list, probably also give 500s.
- **Postgres:** the planned database swap isn't covered.

## What I left behind
- **`fixture/tests/test_threats.py`:** one test per attack. Each passes only once the abuse is refused, so 7 fail right now on purpose. Your original 8 tests still pass. Run them all with `python -m unittest discover tests`.
- **`fixture/.threat/`:** the helper's records. I kept it so that after you fix things, its last check can confirm each attack now fails and comes back if the fix is reverted. Delete it after that, or commit it with the fixes.

<!-- file written by the agent: fixture/.threat/doors.md -->
# Doors

One line per way in that no attack entered: `- DOOR: out: <why>`. A door an attack entered needs no line.

- app.py::__main__: out: only runs when an operator executes app.py by hand; it makes one fixed public GET /catalog call and takes no input
- app.py::r_catalog: out: returns a copy of the price dict, which the README says is public by design (printed price list); takes no input and changes no state
- app.py::r_health: out: returns the constant 'ok'; reads no input and touches no data
