I explain the design and a first implementation plan below. Only `fixture/requirements.md` is in the workspace. `orders/service.py`, `payments/gateway.py`, `db/connection.py` and `web/order_views.py` aren't present, so none of this has been checked against real code. The session budget shows $4, not $8. This used about $0.05.

## Recommended design: refund inside the request, recorded in the existing database

**Do it during the operator's request, and don't add a queue or worker yet.** At 20 refunds a day with no latency target, a queue only adds moving parts: a new service, retry semantics and monitoring. A database record of each refund gives the same safety. This rests on the launch assumptions. If volume grows a lot or the provider turns out to be slow, the same record can later feed a worker without changing what's stored.

**Refunding twice is prevented by data, not by the code flow:**
1. Add a `refunds` table to the existing database through `db/connection.py`. Columns: `id`, `order_id`, `amount`, `idempotency_key` (unique), `status` (`pending` → `succeeded` | `failed`), `provider_refund_id` (unique, nullable), `error`, and timestamps.
2. Create the idempotency key on the server and save it in the same transaction that checks the order is settled. Add a unique constraint that allows only one active (`pending` or `succeeded`) refund per order. A repeated click or form submission then hits the existing row instead of creating a new one.
3. Send that same key to the provider on every attempt, including retries. This assumes the provider supports idempotency keys, which is unconfirmed (see below).
4. Webhooks only update an existing row, matched by `provider_refund_id` or the key. They never start a refund, so a repeated webhook is harmless.

**Unknown provider behavior.** `gateway.py` has no documented response time or retry behavior. So:
- Put an explicit timeout on the call.
- If the call times out or the outcome is unclear, leave the row `pending` instead of marking it `failed`. A "failed" refund that actually went through is exactly how double refunds happen.
- A retry reuses the same row and key. A webhook, or a manual check against the provider, settles the final state.

**What the operator sees.** Show the refund's status on the existing order detail page (completed / failed with reason / pending). Don't add a public status endpoint for now. Its state contract would be visible to callers and hard to change later. The table schema and stored key are already a commitment for data recovery, so they deserve a review before they ship.

## Safe first implementation plan
1. **Read the code first.** Check what `gateway.py` actually does: whether it accepts an idempotency key, whether it retries internally (a hidden retry could double-refund), its timeouts and its error types. Also check how `service.py` handles transactions and the order states, including what "settled" means.
2. **Migration:** add the `refunds` table and its unique constraints. This adds a table without touching existing ones and can be rolled back.
3. **Service:** add `request_refund(order_id, operator)` to `orders/service.py`. It runs in this order:
   - Check the order is settled and claim the `pending` row, in one transaction.
   - Call the gateway with the key, outside the transaction.
   - Record the result: `succeeded`, `failed`, or still `pending` if the outcome is unknown.
4. **Webhook handler:** when the provider confirms or rejects a refund, update the matching existing row. Ignore duplicates. Log events that don't match any refund.
5. **View:** add a refund button and status display to `order_views.py`. The retry action reuses the existing row.
6. **Tests:**
   - Double submission.
   - Concurrent submission (two operators clicking at once).
   - Repeated webhook.
   - Webhook that arrives before the gateway responds.
   - Gateway timeout, then retry.
   - Gateway error, then retry.
   - Order that isn't settled.
7. Release behind a flag or operator permission, and watch for rows stuck in `pending` (an alert or daily report).

## Questions to answer before coding
- **Full or partial refunds?** "Never refund the same amount twice" is ambiguous. I'd start with full refunds only, one per order. Partial refunds need a running total and a different uniqueness rule.
- **Does the provider support idempotency keys?** If not, step 2's protection only works inside our system. A timeout followed by a retry could still double-refund, so unclear cases would need a manual check against the provider before retrying.
- **Who reviews the decisions that are hard to undo?** That's the refund table schema, the stored idempotency key, and whether a status endpoint will ever be public.