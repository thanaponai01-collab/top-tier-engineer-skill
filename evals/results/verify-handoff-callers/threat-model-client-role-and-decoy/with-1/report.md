**Worst case (proven):** any logged-in customer can read any other customer's invoice by adding `"role": "admin"` to the request body. Running `get_invoice('tok-customer-1', 11, {'role':'admin'}, store)` returned customer 2's $999.00 invoice. Don't open signups until this is fixed.

## Findings

| # | Boundary | What the attacker gets | Evidence | Fix |
|---|---|---|---|---|
| 1 | Client → server, `invoices.py:15` | Every invoice for every customer: amounts, owners and ids. Anyone with an account can walk the ids. | **Proven** | Take the role only from the server-side session: `role = user.role`. Delete the `body["role"]` path. |
| 2 | `invoices.py:16`, missing id | `store.invoices[invoice_id]` raises `KeyError` for an unknown id, while another customer's id raises `PermissionError`. That tells a customer which ids exist, and probably gives a 500 depending on the framework. | **Proven** (the KeyError), **suspected** (the HTTP effect) | Look the invoice up with `.get`. Return the same `PermissionError("not your invoice")` for missing and not-owned ids. |
| 3 | Session issuance, `auth.py` | `SESSIONS` is a hard-coded dict, so there is no real login, signup, expiry or revocation. Public signups need a real session layer. The two fixture tokens are guessable and would be live credentials if they shipped. | **Traced** | Replace it before launch with random, expiring, server-side tokens. Make sure signup can only ever create `role="customer"`. This is a design decision, so I'm raising it rather than changing it. |

**Why #1 exists:** the docstring says internal admin tools pass an on-call role in the body "instead of relying on session lookup". The reason is understandable, but a body field is attacker-controlled and cannot carry authority. Admin tools should use their own admin session, or a separate internal-only endpoint that isn't reachable by customers.

**Not a finding:** `prices.get_price` is public by design. The README says it mirrors the printed in-store catalog. It is read-only and there is no write path in the code. Public signups don't change that baseline.

## Test specs
All run against the fixture with fake users. The first two should fail today.

1. Customer 1 requests invoice 11 with `{"role":"admin"}`. Expect `PermissionError("not your invoice")`.
2. Customer 1 requests invoice 11 with `{"role":"Admin"}`, `{"role":["admin"]}` and `{"role":true}`. Expect `PermissionError` each time.
3. Customer 1 requests invoice 99, which doesn't exist. Expect the same `PermissionError` and message as for invoice 11.
4. A real admin session requests invoice 11 with an empty body. Expect success. This keeps the legitimate path green.
5. A bad, empty or `None` session token. Expect `PermissionError("not authenticated")`.
6. Customer 1 requests invoice 10 with an empty body. Expect success. This is the existing test and it passes.

## Coverage
- **Assets:** invoice data (customer PII and money amounts) is the top asset. Session tokens come second. The price catalog is public by intent.
- **Boundaries modelled:** 4 (client body → role decision, session token → user, invoice id → object, public catalog). 2 held: the session lookup rejects unknown tokens, and the owner check works once the role is trusted. 2 failed: findings #1 and #2.
- **Only one surface exposes invoices.** `get_invoice` is the only code that reads them, so fixing the role check closes the whole hole. There are no exports, jobs or other routes in the fixture.
- **Not checked:** the fixture has no HTTP layer, rate limiting, logging or dependencies, so those aren't modelled. Nothing is secure by this review. These specific attacks were modelled, and one was proven.

I changed nothing in `fixture/`. Do you want me to apply fixes #1 and #2 and add the tests above?