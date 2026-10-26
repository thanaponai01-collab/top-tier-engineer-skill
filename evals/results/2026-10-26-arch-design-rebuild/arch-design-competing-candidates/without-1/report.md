I looked at everything in the workspace. That's only `fixture/requirements.md`: `orders/service.py`, `web/order_views.py`, `payments/gateway.py` and `db/connection.py` aren't there. So this plan is based on the requirements alone, and I've marked below what has to be checked in the real code first. Exploration used about $0.04 of the budget.

## Design choice

**Recommendation: refund synchronously inside the request, and record every refund in a new table in the existing database. Don't add a queue or worker.**

**Why not a queue or worker?** At 20 refunds a day, with no response-time target, a queue would add new infrastructure, a new way to fail, and a status endpoint to build, without solving anything we have now. The 20/day figure is a launch assumption, so the design should make it easy to add a worker later. A state table does that: a worker could pick up rows in `pending` without any change to the data.

**Why a persisted refund record?** All three hard requirements depend on remembering what has already happened:
- **No double refund on a repeated request or webhook.** A unique idempotency key on the refund row, plus a row lock on the order, makes a second request find the existing refund instead of creating another.
- **The operator sees completed or failed.** The order detail page reads the refund row's state, so we don't need a status endpoint.
- **Provider failures can be retried safely.** A retry uses the same row and the same key. It never starts a new refund.

**Suggested states:** `requested → submitted → succeeded | failed`, plus `unknown` for a timeout or unclear provider response. Once a refund reaches `succeeded` or `failed` it can't change. `unknown` is the important one: since `gateway.py`'s timing and retry behaviour aren't documented, a timeout must never count as a failure we can blindly retry.

## Decisions that are hard to undo

The requirements already point at these two. They need sign-off before any code:
1. **Refund table schema and idempotency key.** Once real refunds are stored, they're the audit and recovery record. Two choices matter: how the key is built (e.g. a token created when the order page renders, or `order_id + amount + sequence` if partial refunds are allowed), and the unique constraint.
2. **Public refund-state contract.** Keep it internal for now: states shown only on the order page, no API. That keeps the state names free to change.

## Questions to answer before coding (step 0)
- Does the provider accept an idempotency key on refunds? Can we look up a refund by our reference? If neither, a retry from `unknown` has to look up the refund at the provider before sending it again. If the provider supports neither, we can't safely retry automatically, and `unknown` goes to manual review.
- Does the provider send refund webhooks? How are they signed, and what ID do they carry that we can match to our row?
- Are partial or multiple refunds per order allowed? "Never refund the same amount twice" suggests yes, and that changes the key and the uniqueness rules.
- What timeout and retry does `gateway.py` apply now? It must not retry a refund call on its own.
- Who counts as an operator (permissions), and is an audit trail of who refunded what required?

## Implementation plan (small, reversible steps)
1. **Migration:** add a `refunds` table: id, order_id, amount, currency, idempotency_key (unique), state, provider_refund_id, operator_id, error, timestamps. It's purely additive, so it's easy to roll back.
2. **Gateway:** add `refund(order_ref, amount, idempotency_key)` with an explicit timeout and no built-in retry. Return a clear success, failure or unknown result. Add a refund lookup if the provider has one.
3. **Service:** add `orders/service.py: request_refund(...)`. In one transaction: lock the order, check it's settled and that the refund doesn't exceed what's left to refund, then insert the row or return the existing one with that key. Commit, call the gateway outside the transaction, then update the state from the result.
4. **View:** add a refund action on the existing order detail page. The form carries the idempotency token, so a double-click or resubmit reuses the same key. The page shows the refund state, and a retry button appears only for `failed` or `unknown`.
5. **Webhook handler (if the provider has webhooks):** verify the signature, match on provider_refund_id or our key, only move the state forward, and ignore duplicates.
6. **Tests:** double submit, two concurrent submits, provider timeout followed by a retry, duplicate webhook, webhook arriving before the request returns, refund on an order that isn't settled, and amounts that exceed what's left to refund.
7. **Rollout:** put it behind a feature flag and restrict it to an operator role. Start with a few operators and check refunds against the provider dashboard during the first week.

If the provider turns out to be slow enough to time out web requests, step 3 is the only part to change: have it stop after inserting the `requested` row and let a worker pick it up. The schema and the page stay the same.