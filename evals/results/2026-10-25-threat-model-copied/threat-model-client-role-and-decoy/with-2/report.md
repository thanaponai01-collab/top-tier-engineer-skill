**Worst case today (proven):** any customer can read any other customer's invoice by adding `"role": "admin"` to the request body. I ran it: `tok-customer-1` read invoice 11, which belongs to user 2 ($999.00). With the same trick it listed every invoice id in the store.

Both existing tests still pass. Neither one sends a `role` field, so they don't notice the hole.

## Findings, worst first

| # | Boundary | What the attacker gets | Evidence | Fix |
|---|---|---|---|---|
| 1 | Client → server: `invoices.py:15`, `role = body.get("role", user.role)` | Admin read access to every invoice (other people's personal data and amounts) from any self-registered account | **proven** | Take the role only from the server-side session: `role = user.role`. If internal admin tools need an on-call role, issue them admin sessions. Don't let the client declare its own role. Changing who is trusted is a design decision, so whoever owns those internal tools should agree to it before it ships. |
| 2 | `invoices.py:16`: the lookup happens before the ownership check | Lets an attacker tell which invoice ids exist: someone else's invoice gives `PermissionError`, a missing id gives `KeyError: 12`. That leaks invoice count and growth, and if the API returns 403 vs 500 the difference shows up on the wire. | **proven** | Return the same "not found" error whether the invoice is missing or belongs to someone else. |

**Why someone might have built #1 this way:** the docstring says internal admin tools pass their on-call role in the body rather than going through the session lookup. That's a reasonable shortcut for an internal-only caller. Once signups are public, the body is written by whoever sends the request, so a customer can claim admin just as easily.

**Every place that exposes invoices:** `get_invoice` is the only one in `fixture/`. If the real app has invoice lists, exports or PDF endpoints, check each of them for the same `body.get("role")` pattern.

## Checked and held (proven)
- **Forged or unknown session tokens** (`tok-customer-3`, `""`, `None`, a case-changed token) are rejected with "not authenticated".
- **Role variants** (`"Admin"`, `"admin "`, `["admin"]`) are not accepted as admin. Only the exact string `"admin"` works, and that already breaks access control.
- **`prices.get_price`** is public on purpose, per the README: it mirrors the printed catalog. Customer accounts gain nothing new there, so it's not a finding. It's a read-only dict lookup with no injection point.
- **Config/secrets:** no keys or credentials in the source. The session tokens are hard-coded fixture data; make sure a real build doesn't ship with guessable tokens like `tok-customer-N`.

## Abuse-case test specs (each must pass before release)
1. `get_invoice("tok-customer-1", 11, {"role": "admin"}, store)` → raises `PermissionError`. **Fails today.**
2. `get_invoice("tok-customer-1", 12, {}, store)` (id doesn't exist) → raises the same error type and message as test 3. **Fails today:** it raises `KeyError`.
3. `get_invoice("tok-customer-1", 11, {}, store)` → `PermissionError` (passes today, and must keep passing).
4. `get_invoice("tok-customer-1", 10, {"role": "admin"}, store)` → still returns the customer's own invoice. This keeps the legitimate path working after the fix.
5. Unknown, empty or `None` token with `{"role": "admin"}` → `PermissionError("not authenticated")` (passes today).

## Assets
| Asset | Who wants it | What they gain | Worst case |
|---|---|---|---|
| Other customers' invoices | Any registered customer or scraper | Personal and billing data, purchase history | Leak of every customer's invoices |
| Admin privilege | Any customer | Every admin read path | Full escalation (already possible, see #1) |
| Invoice volume (ids) | Competitors | Business metrics | Minor leak |
| Price catalog | Anyone | Nothing; it's already public | None |

**Boundaries:** I modelled 3 (session token → user, request body → authorization decision, invoice id → store lookup). The session token boundary held; the other two failed.

I didn't change anything in `fixture/`. You asked for a threat model, not fixes, and there's no `VERIFY.md` in the project. The attack script is in `../tm-scratch/attack.py` if you want to run it again. When you want the fixes, I can make them and turn specs 1–5 into tests that fail on the current code and pass once it's fixed.