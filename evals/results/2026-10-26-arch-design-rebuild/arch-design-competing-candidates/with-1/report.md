I ran arch-design in design mode and the helper's gate passed (`ARCH-GATE: done`). One caveat first: `fixture/` contains only `requirements.md`. None of the files it names (`orders/service.py`, `web/order_views.py`, `payments/gateway.py`, `db/connection.py`) are there. So this design rests on the written requirements, not on code I read or ran. The finding is rated "suspected" and there is no proof command.

**Verdict:** messy in places. Nothing in the system today can remember that a refund was already requested, so as built, a retry or a repeated webhook would refund twice.

## Finding
- **Where:** `requirements.md:5`, `:7`, `:13`.
- **The gap:** there is no place to store refund state (no refund table, queue or status endpoint).
- **Why it matters:** three things can trigger a refund: the operator's click, the operator's retry, and the provider's webhook. All three would reach `payments/gateway.py` with nothing shared to recognise a duplicate.
- **Unknown timing:** the gateway's response time and retry behaviour aren't documented (`:11`), so a call to the provider has no known time limit.

## Recommendation: save the refund first, then call the provider in the same request
Store a refund record with a unique idempotency key (a key that marks repeats of the same request) in the existing database. Then call the provider directly from `orders/service.py`.

**Safe first implementation plan.** Each step leaves existing order behaviour unchanged, because nothing else reads the new table:
1. **Migration only:** add a `refunds` table with `id`, `order_id`, `amount`, `idempotency_key UNIQUE`, `status` (pending, succeeded or failed), `provider_ref`, `error` and timestamps. It goes in the existing database that `db/connection.py` owns.
2. **`orders/service.py::request_refund(order_id, amount, key)`:** in one transaction, check the order is settled and insert a pending row. The key is the order ID plus a token from the operator's form. If the insert hits the unique constraint, return the existing row instead of starting a second refund.
3. **Call the provider after the commit:** pass the refund row's id as the provider's idempotency key and set an explicit timeout. Record succeeded or failed from the result; on a timeout, leave the row pending.
4. **Webhook handler:** find the row by `provider_ref` or key, and only allow pending to move to succeeded or failed. A repeated webhook then changes nothing.
5. **`web/order_views.py`:** show a refund button on settled orders and the refund's status. Retry reuses the same row and key, so a failed refund can be retried without refunding twice.

**First test, added with step 2:** call `request_refund` twice with the same key against a fake gateway, and check there is one gateway call and one row. Then send the same webhook twice and check the status changes once.

## The fork
This is a one-way door: the table, the stored key, and the refund status operators see all become data and a contract that is hard to change later.

Criteria, most important first:
1. Never refund twice (`:5`, `:7`).
2. The operator sees whether it completed or failed (`:6`).
3. Fewest new moving parts at 20 refunds a day with no response-time target.
4. Moving to background processing later shouldn't need a data migration (`:15`).

The two options:
- **A (chosen): call the provider during the operator's request,** as in the plan above.
- **B: background processing.** Save the row, put a job on a queue, have a new worker call the provider, and have the page poll a new status endpoint.

**Why A:** both options meet criteria 1 and 2 through the same unique-key row. A adds no queue, worker or public endpoint (criterion 3). Criterion 4 still holds, because a worker could later process A's pending rows without any change to them.

**Cost if A is wrong:** if the provider turns out to be slow, you add one worker that finishes pending rows. The table, key and statuses stay as they are, so there's no data migration. Taking B now would mean deploying and monitoring a queue, a worker and a status endpoint for 20 refunds a day. It would also add a second place where a duplicate could slip in: the gap between adding the job to the queue and writing the row.

**Noticed in passing:** two risks for whoever builds this. First, nothing documents how the gateway behaves on retries. Confirm the provider actually honours idempotency keys before step 3, or a retry after a timeout could refund twice. Second, nobody has said who counts as an operator for refunds; the order page needs a permission check before the button goes live.

Nothing in the repo was changed. Should I go deeper on this move, for example confirming the provider supports idempotency keys, or would you rather compare it with option B further first?