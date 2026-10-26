I only explored `fixture/requirements.md`, because that is the only file in the workspace. `orders/service.py`, `web/order_views.py`, `payments/gateway.py` and `db/connection.py` aren't present, so this plan is based on the requirements alone and hasn't been checked against real code. Exploration took about $0.03 and a few minutes, well within the budget.

## Design choice

**Recommendation: handle the refund synchronously inside the request, and record it as a row in the existing database. Don't add a queue or worker.**

Why:
- **Volume and latency don't justify async.** The target is 20 refunds per day and there's no response-time requirement. A queue and worker would be new infrastructure to run and monitor, with nothing gained at launch.
- **The guarantee against double refunds comes from the database, not from the architecture.** A queue still needs idempotency. A database row with a unique idempotency key gives that guarantee whether the call is sync or async. That keeps "move to async later" a cheap change if volume or latency needs grow, since the requirements call these launch assumptions, not limits.
- **It fits the existing shape.** `orders/service.py` owns the action, `db/connection.py` owns the writes, and `web/order_views.py` shows the result on the existing order page. No new public status endpoint is needed.

The core is a `refunds` table and a small state machine:

```
requested ──► provider_pending ──► succeeded
                    │
                    ├──► failed (retryable)
                    └──► unknown (timeout / no response) ──► reconcile before any retry
```

- **Idempotency key:** `UNIQUE(order_id, amount, refund_attempt_scope)`, or simply one active refund per order if v1 is full refunds only. Every request and every retry reuses the same key, and the key is passed to the provider if the gateway supports it.
- **Repeated operator clicks:** the insert hits the unique constraint, and the existing row is returned and shown.
- **Repeated webhooks:** look up by the provider's refund ID and apply the update only if the transition is allowed (`... WHERE status IN (...)`). Duplicate webhooks then do nothing.
- **Retry after failure:** retry only from `failed`. From `unknown`, first ask the provider what happened, then decide. This is the case that actually causes double refunds: a timeout followed by a blind retry.

## Open questions to settle before coding

1. **Does `payments/gateway.py` or the provider support idempotency keys and refund lookup?** This is the biggest risk. If they don't, a timeout leaves us unable to safely retry or confirm the outcome, so `unknown` would need manual reconciliation. Someone needs to read the gateway code and provider docs first.
2. **Two decisions that are hard to undo, which need owner sign-off:** the refund-state names and table schema, and the idempotency key's format. Callers and data recovery will depend on both once they ship. If we keep the states internal and only render them on the order page, the contract stays private for now.
3. **Full or partial refunds in v1?** "Never refund the same amount twice" reads as partial refunds might be needed. I'd suggest full refunds only for v1, which makes the key simply one active refund per order.
4. **Gateway timeout:** since it isn't documented, set an explicit client timeout so that a hung provider call becomes `unknown` instead of hanging the request.

## A safe first implementation plan

1. **Investigate, no code changes:** read the gateway wrapper and provider docs to answer questions 1 and 4, and confirm how webhooks arrive today.
2. **Migration:** add the `refunds` table (`id`, `order_id`, `idempotency_key UNIQUE`, `amount`, `status`, `provider_refund_id UNIQUE NULL`, `error`, timestamps). It's additive only, with no changes to existing tables.
3. **Service:** add `orders.service.request_refund(order_id, operator)`, which:
   - checks the order is settled
   - inserts or gets the refund row in a transaction
   - calls the gateway with the key and records the result as `succeeded`, `failed` or `unknown`
4. **Webhook handler:** make idempotent, allowed-transition-only updates keyed on `provider_refund_id`.
5. **UI:** add a button on the order detail page and show the refund status and error. Offer a retry button only for `failed`, and for `unknown` only after reconciliation.
6. **Tests before rollout:**
   - a double click or concurrent request produces one provider call
   - a duplicate webhook does nothing
   - a timeout ends up `unknown` with no automatic retry
   - retrying after `failed` reuses the same key
   - an order that isn't settled is rejected
7. **Rollout:** put it behind a feature flag for a small set of operators, log every provider call with its key, and do a daily reconciliation report against the provider for the first weeks.

No code has been changed. If you can supply the four referenced source files, I can check the plan against the real code and resolve question 1 first.