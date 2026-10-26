I ran `arch-design` in design mode and the gate passed (`ARCH-GATE: done`). `fixture/` contains only `requirements.md`. None of the files it describes (`orders/service.py`, `web/order_views.py`, `payments/gateway.py`, `db/connection.py`) are there, so this design is based on the requirements alone. I didn't read or run any real code, and nothing in the repo was changed. Spend was about $0.17 and a few minutes, well inside the $8 / 25-minute budget, and no workers were used.

**Verdict:** messy in places. The main risk is that nothing would stop the same refund being sent twice.

## Finding: nothing records that a refund was requested
- **Where:** `requirements.md:5`, `:7`, `:11`, `:13`
- **Problem:** there is no refund table (line 13), so no record exists of a refund having been asked for. Three things could each reach the provider separately: an operator double-click, a webhook the provider sends again, and an operator retrying after a failure (lines 5 and 7).
- **Unknown provider behaviour:** the provider's response time and retry behaviour aren't documented (line 11). If a call times out, we can't tell whether the refund went through.
- **Evidence:** suspected only, because there's no code to check.

## Recommended design: a refund record in the existing database, owned by the order service

**Options compared**, against these criteria in priority order:
1. Never refund the same amount twice, including across retries, repeated webhooks and timeouts.
2. The operator sees "completed" or "failed" on the order page they already use.
3. Refund state has one owner, reusing the existing service and database.
4. Add as little public contract as possible.

- **Option A (chosen):**
  - The order page sends the request straight to `orders/service.py`, which waits for the provider's answer.
  - A `refunds` row in the existing database holds a unique idempotency key: a token that makes a repeated request count as the same request.
  - The provider call has a time limit.
  - Webhooks and retries can only move a refund forward, never back.
  - Status shows on the existing order detail page. There's no new endpoint.
- **Option B:** the page puts a job on a new queue, a worker calls the provider, and the page keeps checking a new public status endpoint.

**Why A:** both options need the unique key and the forward-only states in the database anyway, because that's what actually prevents a double refund (criterion 1). A adds nothing else. B adds a queue, a worker and a public status contract, which is a lot to run for 20 refunds a day (criterion 3).

**Choices that are hard to undo:** the stored refund table and idempotency key. The requirements say these would affect callers and data recovery (line 15), so they deserve review before they ship.

## Safe first implementation plan
Each step leaves current behaviour unchanged.

1. **Table:** add a `refunds` table through `db/connection.py` with these columns:
   - `order_id`, `amount`
   - `idempotency_key` (UNIQUE)
   - `state`: requested → pending → completed or failed
   - `provider_refund_id`, `last_error`, timestamps

   Nothing reads the table yet.
2. **Request:** add `orders/service.py::request_refund(order_id, amount, operator, key)`. It:
   - checks the order is settled and the amount isn't more than what's left to refund;
   - inserts the row and commits. If the key already exists, it returns the existing row and doesn't call the provider;
   - calls `payments/gateway.py` with a time limit, passing the same key if the provider supports one;
   - sets the row to completed, failed, or pending (timed out or unknown outcome).
3. **Webhook:** add `apply_refund_webhook(provider_refund_id, outcome)`. It only moves a refund from requested or pending to a final state, so a repeated webhook does nothing.
4. **Retry:** add `retry_refund(refund_id)`. It only works from failed or pending and reuses the same key. If the provider has no idempotency support, it first asks the provider whether a refund already exists.
5. **Page:** in `web/order_views.py`, show the refund rows and a Refund/Retry button on the existing order detail page. The form carries a key created when the page loads, so a double submit hits the unique key.

**Tests to land with step 2:** there's no code to run checks against yet. Step 2 should come with tests for a repeated request, a repeated webhook, and a retry after a gateway timeout. Each should assert exactly one refund call to the gateway.

## What I'm not doing, and what it costs if I'm wrong
- **Not doing:** a queue, worker and status endpoint now. At this volume, that would mean a message broker to run, secure and back up, a second copy of refund state, and a public contract other code would come to rely on.
- **If A turns out wrong:** if the provider is slow or volume grows, waiting for the provider ties up a web request until the time limit. The fix would be to move step 2's provider call into a background job that reads the same table. That needs no data migration, because the record and its states already exist.

## Open questions to settle before building
- Whether the provider supports idempotency keys. This decides whether step 4 needs the "check the provider first" path.
- The provider's real response time. This sets the time limit.
- Whether partial refunds are in scope. This decides whether "what's left to refund" means summing past refunds.

## Found in passing
No code to review.

Should I go deeper on this design, starting with the provider questions, or work through option B in more detail?