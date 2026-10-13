# Operator refunds: recommended design and first implementation plan

The fixture folder only contains `fixture/requirements.md`. `orders/service.py`, `web/order_views.py`, `payments/gateway.py` and `db/connection.py` aren't in the workspace, so this plan is based on the requirements alone. The plan includes verification steps against the real code. Exploration took one file read, well within your $8 and 25-minute budget.

## Recommendation: synchronous refund call, backed by a refund record in the existing database

- **No queue or worker.** At about 20 refunds per day with no response-time target, a background system adds moving parts without solving a real problem. The operator clicks Refund, the request calls the provider, and the page shows the result.
- **A new `refunds` table in the existing database is the safety mechanism.** It holds `order_id`, `idempotency_key`, `amount`, `status` (`pending` / `succeeded` / `failed` / `unknown`), `provider_refund_id` and timestamps. Put a unique constraint on the order for full refunds, or on the idempotency key. That constraint is what stops a double refund, not checks in application code.
- **Send the same idempotency key to the provider on every attempt**, if the provider supports it. This is what makes "retry without refunding twice" possible.
- **Show the status on the existing order detail page** by reading the refund row. Don't build a public status endpoint yet. The requirements say a public refund-state contract would bind callers, so it should be a separate decision.

The queue/worker option should come back only if the provider proves slow or unreliable, or the volume grows a lot. The `refunds` table works either way, so choosing sync now doesn't block that later.

## The open question that decides safety

`payments/gateway.py` has undocumented response times and retry behavior. Before writing code, find out:

1. **Does the provider accept an idempotency key on refunds?** If not, a retry after a timeout could refund twice. The fallback is to ask the provider for existing refunds on the charge before retrying.
2. **Does the gateway wrapper retry on its own?** Hidden retries plus our retries could duplicate the refund.
3. **What does the refund webhook contain?** It needs an event ID and a refund ID so we can match it to our row and ignore duplicates.

## Safe first implementation, in order

1. **Read the real code (about 15 minutes).** Find how `orders/service.py` handles an order action and its transaction, what `gateway.py` exposes, and whether migrations are in place. Answer questions 1–3 above.
2. **Migration only.** Add the `refunds` table with its unique constraints. Nothing reads it yet, so it can be shipped and rolled back on its own.
3. **Add `orders/service.py::request_refund(order_id, operator)`:**
   - Check the order is settled.
   - Insert or fetch the `pending` row with its idempotency key. A repeated click finds the existing row and doesn't create a second refund.
   - Call the gateway with that key and an explicit timeout.
   - Set the row to `succeeded`, `failed`, or `unknown` (for timeouts and ambiguous errors).
   - Never treat `unknown` as failed.
4. **Retry path.** A retry is only allowed on `failed` or `unknown` rows and reuses the same key. For `unknown`, check the provider for an existing refund first.
5. **Webhook handler.**
   - Look up the row by `provider_refund_id`.
   - Only allow forward state changes (`pending`/`unknown` → final), so a duplicate webhook does nothing.
   - Record processed event IDs.
6. **UI.** Add a Refund button and a status display to the order detail page, with a Retry button shown for `failed`/`unknown`.
7. **Tests:**
   - Double-click and concurrent requests produce one provider call.
   - A duplicate webhook does nothing.
   - A timeout leads to a retry with the same key.
   - Refunding an order that isn't settled is rejected.
   - A provider failure shows up as `failed`.

## Kept out of scope for v1 unless you say otherwise

- **Partial or multiple refunds per order.** The requirement "never refund the same amount twice" leaves open whether this is needed, and it changes the uniqueness rule.
- **The public status endpoint.**
- **Automatic background reconciliation.** For now, retries and fixing `unknown` refunds are manual operator actions.

**Decision needed from you:** confirm whether v1 covers only a full refund per order. If it does, step 2 can start once step 1 confirms how the provider handles idempotency.