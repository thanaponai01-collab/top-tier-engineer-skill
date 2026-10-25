# Threat model: `fixture/` storefront API

**Worst case today (proven):** anyone who signs up can read every customer's invoice by adding `{"role": "admin"}` to the request body.

I ran each attack against the fixture in memory, using its own fake sessions and invoices, from a script kept outside `fixture/`. I didn't change any files. The existing 2 tests pass. They only cover the honest requests, which is why they miss the main bug.

## Findings, worst first

| # | Boundary | What the attacker gets | Evidence | Fix |
|---|---|---|---|---|
| 1 | client → server: who is admin | **Any customer's invoice.** `invoices.py:15` sets `role = body.get("role", user.role)`, so the role is read from the request body instead of the session. | **Proven:** `tok-customer-1` plus `{"role":"admin"}` on invoice #11 returned `owner 2 amount 999.0`. The same request without the role field was rejected. | Take the role only from the session: `role = user.role`. See the design note below. |
| 2 | client → server: invoice id | **Learn which invoice ids exist.** An id that doesn't exist raises `KeyError` (`invoices.py:16`). An existing invoice you don't own raises `PermissionError`. The two responses differ, so ids can be enumerated. | **Proven:** #99 gave `KeyError 99`, #11 gave `PermissionError`. | Use `store.invoices.get(invoice_id)` and return the same error for "not found" and "not yours". |
| 3 | client → server: body shape | **An unhandled 500.** A request body that isn't a JSON object crashes at `body.get`. | **Proven:** `[]` gave `AttributeError`. | Check the body is a dict, or drop the `body` parameter once #1 is fixed. |

Things that held up:
- **No session, no access:** a forged token plus `role=admin` was rejected with "not authenticated", because the session check runs first.
- **Honest requests:** a customer trying to read another customer's invoice without the role field is rejected.
- **Price catalog:** `prices.get_price` is meant to be public according to the README, and it only reads a fixed in-memory dict. An unknown or 10 KB name returns `None`. Opening signups doesn't expose anything new there, so it isn't a finding.

**Why the body role is there:** the docstring says internal admin tools send their on-call role this way. That's the most likely reason. But `auth.SESSIONS` has no admin sessions at all, so the body field is currently the *only* way anyone becomes admin. Removing it locks those tools out until admins get real sessions issued with `role="admin"`. Who counts as an admin is your call, so I haven't made the change. Once signups are public, though, this field gives every new account admin read access.

**Other ways to reach invoices:** `get_invoice` is the only invoice-reading function in the fixture. If the real app has invoice exports, lists, or emails, they need the same ownership check.

**Secrets and config:** there are no keys or credentials in the source. The session tokens in `auth.py` are hard-coded fixture data. If any real deployment issues tokens like that, they're guessable and should be random. There are no dependencies to pin, and no git history to check.

## Abuse-case test specs (add to `test_invoices.py`)

1. `get_invoice("tok-customer-1", 11, {"role": "admin"}, store)` → raises `PermissionError`. **Fails today.**
2. `get_invoice("tok-customer-1", 99, {}, store)` → raises the same `PermissionError` as #11, not `KeyError`. **Fails today.**
3. `get_invoice("tok-customer-1", 11, [], store)` → raises `PermissionError` or `ValueError`, not `AttributeError`. **Fails today.**
4. `get_invoice("bogus", 11, {"role": "admin"}, store)` → `PermissionError("not authenticated")`. Passes today; keep it so it stays that way.
5. Admin path (needs an admin session in `SESSIONS`): an admin token with `{}` on #11 → returns the invoice. This keeps legitimate admin access working after the fix.
6. Existing: customer reads own #10 → returns it. Customer reads #11 with `{}` → `PermissionError`.

## Assets

| Asset | Who wants it | What they gain | Worst case |
|---|---|---|---|
| Invoices (amounts, ownership) | Any signed-up customer | Other customers' purchase history and spending | All invoices read (**reachable now**) |
| Admin authority | Any customer | Bypass every ownership check | Taken with one body field (**reachable now**) |
| Sessions | Anyone outside | Act as a customer | Tokens are fixture literals; can't judge real issuance from this code |
| Price catalog | Anyone | Nothing new; it's public on purpose | None |

**Boundaries:** I covered 4. Session lookup and price lookup held. The role/permission check and the invoice-id/body handling did not.

If you want, I can apply the fixes and add these tests. You'd need to decide first how admin sessions get issued.