# Threat model: `fixture/` storefront API

**The worst thing a customer can do today (proven):** any signed-up customer can read any other customer's invoice by adding `"role": "admin"` to the request body. The server takes the role from that client-supplied field instead of from the session.

I didn't change anything in `fixture/`. My attack script is in a separate directory (`%TEMP%\tm-attacks\attack.py`) and imports the fixture modules. The two existing tests pass, but neither one sends a `role` field, so they don't catch this.

## Findings, by blast radius

| # | Boundary | What the attacker gets | Evidence | Fix |
|---|---|---|---|---|
| 1 | Client request body → permission check (`invoices.py:15`) | Customer 1 sent `{"role":"admin"}` and got back invoice 11 (owner 2, amount 999.00). The same thing works for every invoice. This is trusting the wrong source: the role comes from data the client controls, not from the session. | **proven** (A1) | Use `role = user.role` and ignore `body["role"]`. See the design note below. |
| 2 | Invoice id lookup (`invoices.py:16`) | Invoice ids can be enumerated. A missing id raises `KeyError 12`, while someone else's invoice raises `PermissionError`. That tells a customer which ids exist, roughly how many invoices there are, and how fast they grow. An unhandled `KeyError` probably becomes a 500 error. | **proven** (A4 vs A5) | Look up with `store.invoices.get(id)` and raise the same `PermissionError("not your invoice")` for "missing" and "not yours". |
| 3 | Session tokens in source (`auth.py:8-11`) | The session tokens are static, predictable strings committed to source. They look like fixture data. If real sessions ever work like this, anyone who can read the source gets a login, which would be worse once the source is shared. | **traced** | Issue random tokens at login and store them outside source. If these were ever real, rotate them. |

**Checked and holding:**
- No session, even with `role: admin` in the body, is rejected (A3).
- An honest request for someone else's invoice is rejected (A2).
- `role: null` is rejected (A6).

**Not a finding:** `prices.get_price` is public on purpose (README: it mirrors the printed catalog). It's read-only, does a plain dict lookup, and returns `None` for `*` and `None`. Nothing new becomes reachable through it.

## Design note on fix 1
The docstring says some internal admin tools send their on-call role in the body. The likely reason is that on-call staff don't have an admin session. Removing the body field will break those tools. If they still need access, the decision should be made server-side: give on-call staff real admin sessions, or check the claim against something the server issued (a signed or scoped token), never a plain field.

Before signup opens, apply the same check to every other surface that serves invoices (exports, emails, PDFs, admin pages). Only `get_invoice` is in this fixture.

## Abuse-case test specs (each must pass after the fix)
1. `get_invoice("tok-customer-1", 11, {"role": "admin"}, store)` raises `PermissionError("not your invoice")`.
2. `get_invoice("tok-customer-1", 12, {}, store)` raises `PermissionError`, the same type and message as spec 1, and no `KeyError`.
3. `get_invoice("bogus", 11, {"role": "admin"}, store)` raises `PermissionError("not authenticated")`.
4. To keep allowed behaviour working: customer 1 can still read invoice 10, and a session-backed admin (add `User(id=99, role="admin")` to `SESSIONS` in the test) can read invoice 11 with an empty body.

Today spec 1 fails (the invoice is returned) and spec 2 fails (`KeyError`), which confirms both specs detect the bug.

## Assets
| Asset | Who wants it | What they gain | Worst case |
|---|---|---|---|
| Customer invoices (amounts, purchase history) | Any customer, competitors | Other people's personal and financial data | Every invoice leaks to anyone with an account (**happens today**) |
| Session tokens | Outsiders | Account takeover | Logging in from tokens in leaked source |
| Invoice volume / id space | Competitors | Business metrics | Enumerating ids |
| Price catalog | None | Nothing; it's already public | None |

**Coverage:** I modelled 3 boundaries: request body to authorisation, id to object lookup, and the public catalog. One held (the catalog); the other two failed. Session lookup itself held.

If you want, I can apply fixes 1 and 2 and add the four specs to `test_invoices.py`, after you decide how the on-call tools should get admin access.