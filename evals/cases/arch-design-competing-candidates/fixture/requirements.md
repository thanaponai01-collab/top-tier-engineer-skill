# Operator refunds

## Required behavior
- An operator can request a refund for a settled order from the existing order detail page.
- A repeated request or repeated payment-provider webhook must never refund the same amount twice.
- The operator must see whether the refund completed or failed. The launch target is 20 refunds per day; no response-time target is specified.
- Provider failures must be retryable without charging/refunding twice.

## Existing shape
- `orders/service.py` owns order actions and is called by `web/order_views.py`.
- `payments/gateway.py` wraps the external provider; its response time and retry behavior are not documented.
- `db/connection.py` owns the existing relational database used for order writes.
- There is no queue, worker, refund table, or status endpoint.

The request volume and absence of a latency target are launch assumptions, not proven future limits. A public refund-state contract and persisted idempotency key would affect callers/data recovery if chosen.
