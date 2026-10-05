**Worst case today (proven):** any customer can read any other customer's invoice by adding `{"role": "admin"}` to the request body. I ran it locally: customer 1, using their own token, fetched customer 2's invoice 11 ($999.00).

## Findings

| # | Boundary | What the attacker gets | Evidence | Fix |
|---|---|---|---|---|
| 1 | client body → authorization (`invoices.py:15`) | Every invoice, so all customers' billing data. Invoice ids are small integers, so enumeration is trivial. | **Proven** | Use the role from the session lookup only: `role = user.role`. Delete the body override. |
| 2 | id → existence oracle (`invoices.py:16`) | `store.invoices[invoice_id]` raises `KeyError` for a missing id but `PermissionError` for another user's id. That tells an attacker which ids exist. It will probably also surface as a 500. | **Proven** (`KeyError` observed). The 500 is **suspected** because there is no HTTP layer in the fixture. | Treat a missing invoice and a not-yours invoice the same: raise the same `PermissionError` or a 404 for both. |
| 3 | session issuance (`auth.py:8`) | Nothing exploitable here, but only two hardcoded tokens exist. Real signup, login, token entropy, expiry and revocation aren't in this fixture. | **Traced**, and out of scope as written | Before opening signups, model the real token issuer separately. Tokens must be random, expiring and revocable. |

**Finding 1 is the one that blocks launch.** The docstring says internal admin tools pass the role this way. A competent engineer might have wanted that as a convenience for on-call staff. But it lets the client declare its own permission, and nothing checks the claim. Admin tooling should authenticate as an admin user, with a session whose stored role is `admin`.

**Not a finding:** `prices.get_price` is public by design. The README says it mirrors the printed catalog, and the data is already public. The only thing to confirm is that it stays read-only. There is no write path in the fixture, so a customer can't change prices.

**Other surfaces for the same data:** `get_invoice` is the only invoice surface. Once fixed, any list, export or admin endpoint you add must take the role from the session too.

## Abuse-case tests to add to `test_invoices.py`
1. `get_invoice("tok-customer-1", 11, {"role": "admin"}, store)` must raise `PermissionError`. It currently returns the invoice, so this test fails today.
2. Same call with `{"role": "ADMIN"}`, `{"role": ["admin"]}` and `{"role": None}` must raise `PermissionError`.
3. `get_invoice("tok-customer-1", 999, {}, store)` must raise the same error type as a not-yours invoice (currently `KeyError`).
4. `get_invoice("bogus", 10, {}, store)` and `get_invoice(None, 10, {}, store)` must raise `PermissionError("not authenticated")`.
5. Positive control: a real admin session (a `User(role="admin")` in `SESSIONS`) can still view any invoice, so the fix doesn't break the legitimate admin path.

## Assets
| Asset | Who wants it | Worst case |
|---|---|---|
| Invoice data (amounts, ownership) | Any customer or competitor | Mass disclosure across customers (finding 1) |
| Session tokens | Account takeover | Not modelled; the issuer isn't in the fixture |
| Price catalog | Nobody, since it's public by design | None |

**Coverage:** I modelled 4 boundaries: client body to role, id to invoice lookup, session token to user, and the public price lookup. The public price lookup is intentionally open, and the other three each have a finding above. I didn't change any code. I can apply the fix for finding 1 and add the tests if you want.