SUP-88 is fixed, and a test now catches it. Nothing is committed.

**What was wrong:** `export_csv` in `invoices.py` used whatever `customer_id` came in the request and never checked it against the logged-in user. The accounting integration route (`POST /integrations/accounting/pull`) calls the same function. Its comment says "logged in as staff", but it only checks that someone is logged in. So any customer could pull anyone's invoices through that route too, not only through Export.

**Fix:** In `invoices.py:export_csv`, a customer can only export their own invoices; staff can export anyone's. This is the same rule `get_invoice` already uses. Putting it in the shared function closes both routes. Staff and the nightly accounting pull still work, and there are tests for both.

**Tests:** I added `tests/test_threats.py`. The whole suite passes (21 tests).

## Threat model results (all 10 entry points covered)

**Was open, now closed (3).** Each test failed on the original code, passes now, and fails again if `invoices.py` is put back:
- Any customer exports another customer's invoices (SUP-88): `test_customer_cannot_export_others_invoices`
- A brand-new public signup dumps every customer's invoices: `test_fresh_signup_cannot_export_others_invoices`
- Any customer pulls invoices through the accounting route without being staff: `test_customer_cannot_pull_others_invoices_via_accounting`

**Already refused (6):**
- Reading another customer's invoice.
- Logging in as another user by editing or forging the session token, or using an expired one.
- Logging in without the right password.
- At signup: taking over an existing username (including "Alice" vs "alice"), or giving yourself staff role or extra credit.
- Orders with a negative or zero quantity, an unknown item, or a total above your credit.
- A customer issuing a refund, or staff refunding the same invoice twice.

**No attack needed (3):** `/health` and `/catalog` are public by design and only return fixed data. The `__main__` block only runs from a local shell and takes no input.

## Found but not fixed (outside the ticket)
- **Free credit from fake accounts:** every signup gets 20.00 store credit, with no limit and no verification, and orders spend it on real goods. Once signups are public next week, someone can script accounts and order for free. This needs a product decision before launch, for example credit only after email or payment verification.
- **Passwords are stored and compared in plain text** (`db.User.password`). They should be stored as hashes before real users sign up.
- **A non-ASCII password crashes login:** `hmac.compare_digest` raises `TypeError` (confirmed), and `handle` doesn't catch it, so the request errors instead of returning 401. Hashing the passwords would fix this as well.
- **`SECRET_KEY` changes on every restart if `SHOP_SECRET` isn't set.** Sessions break on restart, and if you run several workers they won't accept each other's tokens. Set it in production.

**Not covered:** these were only read, not attacked: settings and secrets handling, dependencies, concurrency (for example, two orders at once spending the same credit, which would matter once this moves to Postgres), and the real web server in front of `handle`. No secrets are hardcoded in the source.

I deleted the helper's `.threat/` working directory. The new tests stay in `tests/`.