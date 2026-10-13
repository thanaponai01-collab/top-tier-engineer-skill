**Recommendation:** handle refunds synchronously in the request, inside the existing service and database. Don't add a queue, worker or public status endpoint. Before anything else, record each refund attempt in a new refund table, with a uniqueness rule that allows only one refund per order. Use that row both to block duplicate refunds and to show the operator the result.

**What this rests on:** the only file in the workspace is `fixture/requirements.md`. The modules it names (`orders/service.py`, `web/order_views.py`, `payments/gateway.py`, `db/connection.py`) are not in the workspace. Everything below about the code comes from the requirements file and has not been checked against real code. Step 0 of the plan does that check.

## Why this design

| Option | Verdict |
|---|---|
| **Synchronous call, plus a refund row in the existing DB** | **Pick this.** At 20 refunds a day with no response-time target, a queue doesn't help. The database already handles order writes, so the refund row can be written in the same transaction scope as the order. |
| Queue and worker, with a status endpoint | Not now. It adds three new pieces of infrastructure and a public status contract that callers would come to depend on. Add it only if the gateway's response time proves too slow for a web request. |
| Calling the gateway with no saved state | Rejected. It can't stop a second request or webhook from refunding again, and it can't retry safely. |

The design rests on three rules:

1. **Write the attempt to the database before calling the provider.** Insert `refund(order_id, idempotency_key, amount, status='pending')` with a unique constraint on `order_id`. A repeated click or request hits the constraint and gets back the existing row instead of starting a new refund.
2. **A timeout means "unknown", not "failed".** We don't know the gateway's retry or response-time behavior. If a call times out, the provider may already have refunded the money. That row stays `pending`, and a retry must first check the provider's state (or resend the same idempotency key) rather than starting a fresh refund.
3. **Webhooks only update rows that already exist.** Store the provider's refund or event id under a unique constraint. Move the status only forward (`pending` → `succeeded` / `failed`). A repeated webhook then does nothing.

The operator sees the status on the order detail page, which reads the refund row. That keeps the refund state internal. A public refund-state contract can still be added later. The new table and its idempotency key do change the database permanently, so the migration needs sign-off.

## Questions to answer before coding

1. **Does the payment provider accept an idempotency key, and can we look up a refund by that key?** This is the most important one. If it can do neither, a timed-out refund can't be retried automatically and needs manual reconciliation.
2. **Full refunds only, or partial refunds too?** The requirement says "never refund the same amount twice", which is ambiguous. The one-refund-per-order constraint assumes full refunds only. Partial refunds would need a running total instead.
3. **How are webhooks authenticated, and where do they come in?** No webhook handler is listed in the existing code.

## Safe first implementation plan

Each step has a check, and the check is written before the code.

0. **Check the real code.** Read `orders/service.py`, `web/order_views.py`, `payments/gateway.py` and `db/connection.py`. Find what calls each one, how the gateway sets timeouts and raises errors, and how migrations are run. *Check:* each assumption above is confirmed or corrected in writing.
1. **Migration for the new `refund` table.** Unique on `order_id` and on `provider_refund_id`, with a status column. *Check:* the migration applies and rolls back cleanly on a copy of the database.
2. **`orders/service.py: request_refund(order_id, operator)`.** Reject orders that aren't settled. Insert or fetch the refund row, call the gateway with the key, and record the result. A timeout leaves the row `pending`. *Check:* tests for a double call (one gateway call), a timeout followed by a retry (the same key is reused, no second refund), and a non-settled order (rejected).
3. **Webhook handler.** It looks up the row and only moves the status forward. *Check:* sending the same webhook twice changes nothing the second time, and an out-of-order event doesn't move the status backwards.
4. **Order detail page.** Add a refund button and show the status from the row, including "pending, being checked". *Check:* a view test covers each state.
5. **Rollout.** The table only adds new things, so if needed the button can be hidden and the table left in place. Nothing calls the provider until step 2 ships. Refunds move real money, so test against the provider's sandbox before production, and only with your sign-off.

No code has been changed. I suggest starting with step 0 and question 1 together, because the provider's idempotency support decides how step 2 handles retries.