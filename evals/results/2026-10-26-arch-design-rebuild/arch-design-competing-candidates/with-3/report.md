I recommend handling the refund directly inside the order service, with a new `refunds` table where each refund has a unique idempotency key (an ID that lets the system recognise a repeated request). I'd skip a queue, a background worker and a public status endpoint for now. I wrote this from `fixture/requirements.md` alone: `fixture/` has no code, so `orders/service.py`, `payments/gateway.py`, `db/connection.py` and `web/order_views.py` are only described there. That means there was nothing to run as a test and no callers to list. The skill's completion check passed (`ARCH-GATE: done`) and nothing in `fixture/` was changed.

## The problem
Nothing records that a refund was attempted (`requirements.md:13`: no refund table, no status endpoint). So a repeated operator request, a repeated provider webhook (the provider's callback) and a retry after a provider failure each look like a new refund. All three no-double-refund requirements (`requirements.md:5`, `:7`) depend on stored refund state, and nothing stores it today.

## Recommended structure
- **New `refunds` table** in the existing database (`db/connection.py`), with these columns:
  - `order_id`
  - `idempotency_key`, unique
  - `amount`
  - `status`: `requested`, `succeeded` or `failed`
  - `provider_ref`
  - `error`

  Add a check that the refunded amounts for an order never exceed what was settled.
- **`orders/service.py::refund_order(order_id, amount, key)`**: in one transaction it creates the row, or returns the existing row if this key was already used. It then calls the gateway with the same key and records whether the refund succeeded or failed.
- **The gateway** passes the key on to the provider, so the provider also ignores repeats.
- **The webhook** finds the row by key or `provider_ref` and only moves it from `requested` to `succeeded` or `failed`. A webhook arriving for a row that has already finished is ignored.
- **The order detail page** gets a refund button and shows the row's status. The key is generated when the form is shown, so a double-submit reuses it.

## Why this over a queue and worker
I ranked the criteria first:
1. Never refund twice.
2. The operator sees whether it completed or failed.
3. Fewest new moving parts.
4. Easy to change later.

Both designs meet 1 and 2 the same way: the refunds table and the key do that work. The queue design adds three parts (a queue, a worker deployment, and a public status contract that other code would depend on). That isn't justified at 20 refunds a day with no response-time target.

If it turns out wrong, for example the provider is slow (its timing isn't documented, `requirements.md:11`), a worker can be added later that reads the same rows. No data migration would be needed.

This is a one-way door, because the stored refund data and keys are hard to change once real refunds exist. That's why the table design should be agreed before writing code.

## Safe first implementation plan
Each step leaves current behaviour unchanged:
1. **Add the table** with the unique key and the amount check. Nothing reads it yet.
2. **Add an optional `idempotency_key` to the gateway's refund call.** Without it, the call behaves as it does today.
3. **Add `refund_order()`**, with a test that calls it twice and replays the webhook twice using the same key. The test must show exactly one call to the gateway and one `succeeded` row. This is the proof the fixture couldn't provide.
4. **Make the webhook handler update the row only from `requested`.**
5. **Add the button and status to the order detail page.** No new endpoint.

## Things to settle before step 1
- **Provider support:** confirm the provider actually accepts an idempotency key. If it doesn't, a timed-out call can't safely be retried. The only safe path is to leave the row as `requested` and let the webhook or a status lookup settle it.
- **Pending status:** the requirements only mention completed and failed, but a call that times out leaves the refund pending. The page needs to show a pending state, with a timeout on the gateway call.

I found no bugs or security holes, since there is no code. This was a single run in a few minutes and well under the $8 budget.

Is this the direction you want, or should I explore the queue-and-worker option further?