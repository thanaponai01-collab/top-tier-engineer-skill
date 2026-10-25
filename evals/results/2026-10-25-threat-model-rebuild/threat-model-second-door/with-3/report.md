I've fixed SUP-88, and the customer was right. Any logged-in customer could export anyone's invoices by changing `customer_id` in the export request. The same hole was also open through a second route, `POST /integrations/accounting/pull`. That route is only meant for the nightly accounting sync, but it accepted any logged-in user, so a plain customer could use it the same way. Nothing is committed.

**Cause and fix.** `invoices.export_csv` exported whatever customer number it was given, without checking who was asking. I added the ownership check that `get_invoice` already has (`fixture/invoices.py:18`): you can export your own invoices, staff can export anyone's, and everyone else gets a 403. Both routes go through this one function, so the single check closes both. Exporting your own invoices still works, and so does the staff accounting sync.

**Tests that would have caught it** are in `fixture/tests/test_attacks.py`:
- `test_export_other_customer_refused`: the ticket's exact steps. Alice exports with `customer_id: 2` and must get a 403, with none of Bob's invoices in the response.
- `test_customer_cannot_use_accounting_pull`: the same attack through the sync route.
- `test_staff_export_any_customer` and `test_accounting_pull_as_staff`: staff and the nightly sync can still export any customer.

The two attack tests failed on the old code and pass now. With only `invoices.py` put back, both fail again, which shows they really detect the bug. The full suite passes: 17 tests, the 8 originals plus 9 new.

**Threat model of `fixture/`:** the helper found 10 routes and entry points.
- **Open, now fixed (2):** the export route and the accounting-pull route above.
- **Already refused (5):** I tried these attacks and kept each one as a test:
  - reading another customer's invoice by its number;
  - a customer refunding their own invoice, or staff refunding the same invoice twice;
  - orders with a negative or zero quantity, an unknown item, or a total above the customer's credit;
  - forged or altered login tokens, and logging in with a wrong password;
  - signing up as "ALICE" to take over Alice's account, or sending `role: staff` or a credit amount with the signup.
- **Not attacked, because there's nothing to gain (3):** `GET /catalog` (public on purpose, per the README), `GET /health` (always returns "ok"), and running `app.py` from a shell.

I didn't claim the app is secure, only that these attacks were run and came out as listed.

**Not covered, and worth deciding on before signups open next week:**
- **Free credit from fake accounts:** every signup gets $20 of credit, and signup has no rate limit, email check or CAPTCHA. Once signups are public, anyone can script thousands of accounts and spend the credit on real orders. This is a business-rule question, so I didn't change it.
- **Plain-text passwords:** they're stored as typed (`db.User.password`) and should be hashed.
- **No brute-force protection on login:** nothing limits repeated password attempts.
- **Secret key setting:** if `SHOP_SECRET` isn't set, `settings.SECRET_KEY` is generated at random on each start. All logins then break on every restart and won't work across multiple servers, so set it in production.
- **Crash on a bare `GET /invoices`:** with no invoice number it raises an `IndexError` the app doesn't catch, so the server returns an error page instead of a 400.
- **Only read or not checked:** the code assumes one request at a time, so I didn't test two requests spending the same credit at once. That becomes relevant when the in-memory data is swapped for Postgres.

The helper's scratch folder `.threat/` and the `__pycache__` folders from running the tests are deleted. The new test file stays in `fixture/tests/`.