**Recommendation:** process refunds synchronously in the existing request path, and store each refund in a new table in the existing database. Don't add a queue or worker. The refund row is what prevents double refunds: it's written before the provider is called, and every retry and webhook goes through it.

**What this rests on:** the workspace only contains `fixture/requirements.md`. There is no `orders/service.py`, `payments/gateway.py`, or `db/connection.py`, so everything I say about the codebase comes from that document, not from reading the code. The first step of the plan is to read the real code. This took about $0.08. Also, this session's budget is $2, not the $8 you mentioned, so I kept exploration minimal.

## Design choice

| Option | Verdict |
|---|---|
| **Synchronous call + refund table in the existing DB** | **Pick this.** At 20 refunds a day with no response-time target, a queue buys nothing, and it adds infrastructure that doesn't exist yet. The refund row gives the same protection against double refunds. |
| Queue + worker | Not yet. It's easy to add later: a worker can pick up `pending`/`unknown` rows without changing the table or the UI. Revisit if volume grows or the provider turns out to be slow. |
| No persisted state, rely on provider idempotency only | No. You couldn't show the operator what happened, recover after a crash, or handle repeated webhooks. |

**How a refund flows:**
1. In one transaction: lock the order row, check it is settled and has no open or succeeded refund, then insert a refund row (`status=pending`, `idempotency_key`, `amount`). A unique constraint stops two requests that arrive at the same moment from both getting through.
2. Commit, then call the gateway with a timeout, passing the idempotency key.
3. Record the outcome: `succeeded` or `failed`. If the call timed out or the provider's answer is unclear, record `unknown`, not `failed`.
4. **Retry:** first ask the provider what happened to this key or charge, then reuse the *same* key. Never generate a new key for the same refund.
5. **Webhook:** find the refund by provider refund id or key. Status only moves forward (`pending`/`unknown` → `succeeded`/`failed`), so a repeated webhook does nothing.
6. **Showing the result:** the existing order detail page reads the refund row. I'd skip a new public status endpoint for now, because the requirements say a public refund-state contract would affect callers.

## Decisions to make before coding
1. **Does the provider accept idempotency keys, and can you look up a refund's status?** This is the biggest unknown, because `gateway.py`'s behavior isn't documented. If neither is available, the only protection on retry is checking the provider's refund list for the charge first. Check this before anything else.
2. **Webhooks:** the requirements mention provider webhooks, but no webhook handler is listed in the existing code. Does one exist, or is it new?
3. **Full or partial refunds?** I recommend full refunds only for the first version. Partial refunds need a check that the total refunded never exceeds the charge.
4. **Sign-off on two hard-to-reverse choices:** the refund table schema, and the idempotency key format. Once refunds are stored with those keys, changing either becomes a data migration problem. The requirements flag both.

## First implementation plan
0. **Read the real code** (no code changes): `orders/service.py`, `web/order_views.py`, `payments/gateway.py` (timeouts, built-in retries, idempotency support), and `db/connection.py` (transactions and locking). If the gateway already retries on its own, that has to be turned off or made to use the same key. Otherwise its own retries could refund twice.
1. **Write the acceptance tests first** and confirm they fail:
   - two refund requests for the same order at the same time → exactly one gateway call;
   - the same webhook delivered twice → one status change, one refund;
   - gateway times out, then a retry → the provider sees the same key, and only one refund happens;
   - gateway fails → the order page shows "failed" and a retry is allowed;
   - an order that isn't settled → rejected.
2. **Add a migration for the refund table**, with its unique constraint. It should apply and roll back cleanly.
3. **Add the gateway refund call** with an explicit timeout, the key passed through, and a status lookup.
4. **Add the refund action in `orders/service.py`**, following the flow above. `web/order_views.py` only calls it and renders the status.
5. **Add the webhook handler or reconciliation**, depending on the answer to decision 2.
6. **Add a small reconcile step**, either a script or a button, that resolves `unknown` rows by asking the provider.

The tests in step 1 define "done." The first real refund against the live provider affects actual money, so it needs explicit approval and a test order. No code has been changed yet.