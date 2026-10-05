**Worst case (proven):** any logged-in customer can read any other customer's invoice by adding `"role": "admin"` to the request body. I ran it against the fixture with fake data: customer 1's token read invoice 11, which belongs to customer 2, and got amount 999.0. The existing tests still pass (2/2) because neither one sends a `role`.

## Findings (by blast radius)

| # | Boundary | What the attacker gets | Evidence | Fix |
|---|---|---|---|---|
| 1 | Client body → authorization decision (`invoices.py:15`) | Every invoice for every customer. The invoice IDs are sequential and guessable, so this is a full scrape. | **Proven** | Delete `body.get("role", ...)` and use `user.role` from the server-side session only. |
| 2 | Invoice lookup (`invoices.py:16`) | A missing ID raises `KeyError`, while someone else's ID raises `PermissionError`. That difference lets a customer find out which invoice IDs exist. A real handler will also probably return a 500 for the `KeyError`. | **Proven** (`KeyError` on id 999) | Use `store.invoices.get(id)`. Return the same "not found / not yours" error for both cases. |
| 3 | Session store (`auth.py`) | Nothing exploitable today: the tokens are hardcoded and there are only two of them. Public signup needs real issuance, and the fixture has none. | **Traced** | Tokens must come from a CSPRNG (e.g. `secrets.token_urlsafe(32)`) and carry an expiry. Store only hashes, and never put a role in the token or the request. |

**On the `role` field:** the docstring says internal admin tools pass their on-call role in the body. That may be a convenience for those tools, but it works only because the server believes the client. Admin tools should authenticate as admin users, so their session lookup returns `admin`.

**On `get_price`:** I did not flag the missing login. The README says it's intentionally public and mirrors the printed catalog, so I treated that as the baseline. Two things to check before launch. `get_price` is read-only, so no price can be changed through it. Once signups open, you'll want rate limiting on it, which this fixture can't show.

## Abuse-case test specs

These should be added to `test_invoices.py`. Tests 1 and 2 should fail today. Test 3 reproduces the `KeyError` found in #2. Test 4 should already pass.

1. **Forged role:** `get_invoice("tok-customer-1", 11, {"role": "admin"}, store)` must raise `PermissionError`.
2. **Other role values:** the same call with `{"role": "ADMIN"}`, `{"role": ["admin"]}`, and `{"role": None}` must raise `PermissionError`. Today `None` raises `KeyError` only because of the lookup in #2.
3. **No existence oracle:** requesting ID 999 and requesting someone else's ID 11 must raise the same exception type with the same message.
4. **Auth:** an unknown or empty token and `None` must raise `PermissionError`. Right now this test should pass.
5. **Surface parity:** whatever layer eventually exposes invoices (list, export, PDF, webhooks) needs the same ownership test. This fixture has only one surface, `get_invoice`, so there's nothing else to check yet.

## Assets

| Asset | Who wants it | Worst case |
|---|---|---|
| Invoices (amounts and owner IDs, probably PII once real) | Any customer account | Mass cross-customer disclosure (#1) |
| Session tokens | Outsiders | Account takeover once real issuance exists (#3) |
| Price catalog | Anyone | Nothing, since it's public by design |

## Coverage

I modelled 4 boundaries: client body, session lookup, invoice store, and the public price lookup. Of those, 2 held (the price lookup, which is public by design, and auth rejecting unknown tokens). Finding #1 broke the client-body boundary, and the session lookup only holds because the tokens are hardcoded (#3).

This covers only the six files in `fixture/`. There's no HTTP layer, no token issuance, and no rate limiting in it, so none of those were assessed. I didn't change any code. I can apply #1 and #2 and add the tests if you want.