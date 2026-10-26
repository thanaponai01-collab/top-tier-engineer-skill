# Operator refunds: design choice and a safe first plan

**Note on what I could check:** the workspace contains only `fixture/requirements.md`. The files it names (`orders/service.py`, `web/order_views.py`, `payments/gateway.py`, `db/connection.py`) aren't here, so this plan is based on the requirements alone. Things I couldn't confirm are listed as open questions below. I spent about $0.04 and a few minutes, well inside your budget.

## Recommendation: refund in the request, backed by a refund record

When the operator clicks refund, the request calls the provider directly. Before that call, it saves a refund record keyed by an idempotency key. No queue or worker for now.

**Why not a queue or worker:**
- 20 refunds a day with no response-time target doesn't need background processing.
- No queue or worker exists today, so adding one means new infrastructure, deployment and monitoring.
- The requirements call the volume and latency figures assumptions, not limits. A refund record keeps the queue option open: a worker could later pick up records in `pending` without changing the data.

**Why the refund record is required:** the duplicate-refund and retry rules can't be met without stored state. Each requirement maps to one mechanism:

| Requirement | Mechanism |
|---|---|
| A repeated click or webhook never refunds twice | A unique idempotency key on the refund record, and the same key sent to the provider |
| The operator sees whether it completed or failed | The record's status, shown on the existing order detail page |
| Retries never refund twice | A retry reuses the same key when the outcome is unknown, and only advances the existing record |

## Main risk: the provider's response is undocumented

We don't know how fast `payments/gateway.py` responds or how it retries. So a timeout has to be treated as **"unknown"**, never as "failed". If a timeout were recorded as failed, the operator could retry with a new key and refund the customer twice.

The status flow:

```
requested ──► pending (key saved before the provider call)
pending ──► succeeded | failed (provider gave a definite answer)
pending ──► unknown (timeout or error) ──► resolved by webhook, or retried with the SAME key
```

- A new key is issued only after the provider confirms that no refund happened.
- Webhooks are deduplicated by the provider's event or refund ID. They only move a record forward to a final status and never start a refund.
- Two operators clicking at once: in one transaction, lock the order row and insert the refund record. The unique constraint makes the second click return the existing record.

## Decisions that are hard to undo (agree on these before writing code)

1. **Refund table schema and idempotency key format.** These affect data recovery and are expensive to change once rows exist. Suggested shape: `id, order_id, amount, currency, idempotency_key UNIQUE, provider_refund_id UNIQUE NULL, status, last_error, created_at, updated_at`.
2. **Public refund-status contract.** I'd **not** add one in v1. Show the status only on the order detail page and keep the status names internal, so they can still change. A public status endpoint can come later, once a caller actually needs it.

## Open questions to answer first

- Does the provider accept idempotency keys? If not, the plan needs a "check with the provider before retrying" step instead. This is the biggest single factor in the design.
- Is there an existing webhook handler, and does it verify signatures?
- Full refunds only, or partial refunds too? "Never refund the same amount twice" hints at partials. Partials change the key from one per order to one per operator request, plus a check that the total refunded never exceeds the amount charged.
- What does "settled" mean in the order model, and what happens to the order's own status after a refund?
- Which operators are allowed to refund (permissions and audit trail)?

## Implementation plan (each step can ship on its own)

1. **Investigate, without changing code.** Read the gateway wrapper and provider docs for idempotency, timeouts and webhook behavior. Answer the open questions above.
2. **Add the refund table.** A migration through `db/connection.py`'s existing database, with the unique constraints. Nothing uses it yet, so it's easy to roll back.
3. **Add `request_refund(order_id, operator, ...)` to `orders/service.py`.** It checks the order is settled, locks the order, creates or returns the refund record, saves it as `pending`, then calls the gateway with the key and records the outcome. Put it behind a feature flag.
4. **Gateway changes:** pass the idempotency key, set an explicit timeout, and return a definite success, a definite failure, or "unknown". It should not retry automatically.
5. **Order detail page (`web/order_views.py`):** add the refund button and status display. The button is disabled while a refund is in progress or done, and an operator can retry only `failed` or `unknown` records.
6. **Webhook handling:** deduplicate events and only move records forward to a final status.
7. **Tests before turning the flag on:** a double click, two simultaneous requests, a replayed webhook, a webhook arriving before the provider's response, a timeout followed by a retry, and a definite failure followed by a retry. Each must end in at most one provider refund. Use a fake gateway that can delay, time out and replay.
8. **Rollout:** turn it on for a few operators, and set an alert for records stuck in `pending` or `unknown` too long.

Once the open questions are answered, start with steps 1 and 2. Agree on the schema and key format in step 2 before writing service code.