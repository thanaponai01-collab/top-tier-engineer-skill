I ran the threat model on `fixture/`. A customer account, or someone with no account, can make the shop do six things it shouldn't. Each one was actually carried out, not just spotted by reading the code. Nothing is fixed yet, as you asked.

**What can be done today, worst first:**

1. **Any customer can give themselves unlimited store credit.** Ordering a negative quantity (e.g. `gadget` × -1000) gives a negative total. Subtracting that from their balance *adds* about $20,000 of credit, which they can then spend on real goods. Every free signup can do this. The code is in `orders.py:15-23`. Fix: in `place_order`, reject any quantity below 1.
2. **Anyone who has seen the source can make themselves staff.** The key that signs login tokens is hard-coded in `fixture/settings.py:1` (it's a hard-coded token-signing key; I'm not repeating its value here). With it, the test made a staff token for user 3 and issued a refund. That person could also read every invoice. Fix: **rotate the key**, load it from the environment or a secret store, and assume anything signed with the old key is compromised.
3. **Any customer can download any other customer's invoice history.** `POST /invoices/export` uses whatever `customer_id` the request sends, and `export_csv` never checks who is asking. In the test, bob got alice's invoices. Fix: in `invoices.export_csv`, apply the same owner-or-staff check `get_invoice` already uses.
4. **Anyone can take over an existing username.** Signup checks whether the name *as typed* is taken, but saves it lowercased (`auth.py:35-39`). Signing up as `Alice` replaces alice: her password now logs in nobody, her old tokens stop working, and she can no longer reach her invoices. The same works on staff names like `Sam`. The new account is a plain customer, so it gains no staff powers, but the real owner is locked out. Fix: lowercase the name once at the start of `signup` and use that for both the check and the save. (A side effect: if the original user's record is gone, refunding their invoice crashes `orders.refund`.)
5. **Anyone, logged in or not, can crash a request with a non-ASCII login token.** `hmac.compare_digest` raises `TypeError` when given non-ASCII text, and nothing in `app.handle` catches it. Fix: in `auth.current_user`, compare bytes, or treat any non-ASCII token as invalid.
6. **Anyone can crash login the same way with a non-ASCII password** (`auth.py:45`). Fix: compare the encoded bytes, which pairs naturally with storing password hashes instead of the passwords themselves.

**Ways in with nothing behind them:** `GET /catalog` is public by design and only returns a copy of a fixed price list. `GET /health` always returns "ok". The `__main__` block only runs when someone starts `app.py` by hand. None of them takes input an attacker could use.

**Not tested (only read, or out of reach):**
- Passwords are stored in plain text (`db.py`).
- There is no password rule (`"x"` is accepted) and no limit on login attempts, so passwords can be guessed by brute force.
- Signups are unlimited and each one gets $20 of free credit, which is free stock even without the negative-quantity trick.
- An invoice that doesn't exist returns 400 while someone else's returns 403, so customers can tell which invoice IDs exist.
- Two simultaneous orders could race on the credit balance; this only matters once the in-memory store is replaced by Postgres.
- I didn't check dependencies or deployment settings.

**Status:** all six attacks are kept in `fixture/tests/test_attacks.py`. They run with the normal `python -m unittest discover tests`, which means the suite fails today: 6 failures, while the original 8 tests still pass. That is intended. Each one starts passing when its hole is closed and fails again if a later change reopens it. I left the `.threat/` folder in place so that after the fixes the helper can confirm each fix is what closed its hole. You can delete it, or commit it with the fixes.

<!-- file written by the agent: fixture/.threat/doors.md -->
# Doors

One line per way in that no attack entered: `- DOOR: out: <why>`. A door an attack entered needs no line.

- app.py::__main__: out: runs only when an operator executes app.py by hand; it makes one fixed GET /catalog call, takes no input, and no web request can reach it
- app.py::r_catalog: out: public by design (README: the printed price list); ignores headers, body and args, and returns a fresh copy of a constant dict, so there is no input to steer and nothing private to reveal
- app.py::r_health: out: ignores headers, body and args and returns the constant "ok"; nothing to steer and nothing to reveal
