I ran arch-design in design mode and its gate passed (`ARCH-GATE: done`). One caveat first: `fixture/` contains only `requirements.md`. There is no code, so the modules it mentions (`orders/service.py`, `payments/gateway.py`, `db/connection.py`, `web/order_views.py`) come from that document, not from code I read. That's why no proof command could be run; one is suggested below. Nothing in `fixture/` was changed, and the exploration used about $0.18 and a few minutes.

**Verdict:** the existing structure is clean, but it has nowhere to record that a refund happened. As a result, a double-click, a retry or a repeated provider webhook could each send a second refund.

## The problem
- **Where:** `requirements.md:5`, `:7`, `:13`
- **Evidence:** suspected. There is no code to run or trace.
- **Cost:** there are 0 places that store a refund or an idempotency key, and 0 places where the operator can see the result.

## Recommended design: save a refund record before calling the provider, in the existing service and database

**Option A (chosen):** handle the refund synchronously in `orders/service.py`.
- Add a new `refunds` table in the existing database (`db/connection.py`) with these columns:
  - `order_id`
  - `idempotency_key` (UNIQUE)
  - `amount`
  - `state`: `pending | succeeded | failed | unknown`
  - `provider_refund_id`
  - `error`
- The UNIQUE key is what prevents duplicates.
- The provider's webhook updates the existing row; it doesn't start a new refund.

**Option B (rejected):** a queue, a worker and a status endpoint.

**How I chose.** Criteria, ranked:
1. Never refund twice.
2. The operator sees completed or failed.
3. Add as little new infrastructure as possible: launch is 20 refunds a day with no response-time target.
4. Keep it easy to move to async later.

I picked A because of criterion 3. It covers 1 and 2 with the same table B would need anyway, and it adds no queue, worker or new public endpoint. If the provider turns out to be slow or volume grows a lot, the table and the states stay as they are. Only the provider call moves into a worker, so roughly one file changes, plus the new queue and worker.

**This is a one-way door.** Once stored, refund rows and idempotency keys are needed for recovery and audit, and the refund states shown to operators become something people rely on. Settle the state names and the key format before the first deploy.

## Safe first implementation plan
Each step leaves current behaviour unchanged until the button ships.

1. **Migration:** add the `refunds` table. Nothing reads it yet.
2. **`orders/service.py::refund_order(order_id, amount, key)`:**
   - Check that the order is settled.
   - Insert the row. If the key is already there, return the existing row instead of refunding again.
   - Call `payments/gateway.py` with an explicit timeout, passing the key to the provider if it accepts one.
   - Save the result. **On a timeout, save `unknown`, not `failed`.** We don't know whether the provider processed it.
3. **`web/order_views.py`:** add the button and a result display to the order detail page. Generate the key once per form, so a double-click or resubmit reuses it.
4. **Webhook handler:**
   - Find the row by `provider_refund_id`.
   - Only move the state forward (`pending`/`unknown` to `succeeded`/`failed`).
   - Ignore repeats.
5. **Retry:** allow it only from `failed` or `unknown`.
   - First ask the provider whether that refund exists.
   - Send a new refund only if the provider confirms it doesn't.

**Proof to add before step 2:** three tests against a fake gateway:
- `test_refund_twice_same_key_calls_gateway_once`
- webhook replay is a no-op
- a timeout followed by a retry does not refund twice

## Risks worth checking before building
- **The gateway's timeouts and retries aren't documented (`requirements.md:11`).** Steps 2 and 5 depend on two things the provider must support:
  - accepting an idempotency key, or
  - letting us look up a refund by our reference.

  If it supports neither, a timeout can't be resolved safely in code. The `unknown` state then has to go to a person to sort out by hand. Confirm this with the provider first.
- **Partial refunds aren't mentioned in the requirements.** If they're allowed, also check that the total refunded can never go over the order amount, enforced inside the same database transaction.

Should we explore this move further, starting with the provider's support for idempotency keys? Or would you rather look at the async option in more depth?