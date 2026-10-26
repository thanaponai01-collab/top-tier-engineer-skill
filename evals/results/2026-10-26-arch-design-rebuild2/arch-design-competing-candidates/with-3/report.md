I recommend recording each refund as a row in the existing database, with a unique key that stops it running twice, and having `orders/service.py` call the provider directly. Don't add a queue, a worker or a public status endpoint for now. The arch-design gate passed (`ARCH-GATE: done`), and nothing in `fixture/` was changed.

One thing limits all of this: `fixture/` contains only `requirements.md`. There is no code, so the design rests on that document alone. I couldn't trace any code, list its callers or run a test against it. The finding below is a likely risk, not a confirmed bug.

## The problem
Nothing stores refund state today (`requirements.md:13`: no refund table). So a repeated click, a retry or a repeated webhook (`:5`, `:7`) each risk another provider refund. The gateway's timeout and retry behaviour isn't documented (`:11`). After a timeout we wouldn't know whether the refund went through, and we'd have no record to check.

## Design choice
| Criterion (ranked) | A: refund row + synchronous call | B: queue + worker + status endpoint |
|---|---|---|
| 1. Never refund twice | Yes, via the unique key | Yes, but only with the same unique key |
| 2. Operator sees completed or failed | Shown on the existing order page | The page polls a new endpoint |
| 3. Fewest new things to run and keep compatible | Adds one table | Adds a queue, a worker and a public API contract |
| 4. Room to grow past 20 refunds a day | A worker can be added later on the same table | Already in place |

**Choose A, because of criterion 3.** Both options only prevent double refunds through the stored unique key, so the queue adds nothing on correctness. At 20 refunds a day with no response-time target, it would just be one more thing to run, secure and monitor. It would also publish a refund-status contract that callers would depend on, which `:15` warns about.

The table is a decision that's hard to undo. If it's wrong, for example missing the unique key, fixing it means a data migration and possibly double refunds already sent. Rejecting the queue is easy to revisit: if the provider turns out to be slow, a background job can retry the `pending` rows on the same table, with no data migration.

## Safe first implementation plan
Each step leaves current behaviour unchanged until step 4 adds the button.
1. **Migration:** add a `refunds` table with `order_id`, `amount`, `idempotency_key` (unique), `status` (`requested`, `pending`, `succeeded` or `failed`), `provider_ref`, `error` and timestamps. It uses the existing database through `db/connection.py`. Nothing reads it yet.
2. **Gateway:** add `payments/gateway.py::refund(order, amount, idempotency_key)` with an explicit timeout, and pass the key to the provider. It isn't called yet.
3. **Service:** add `orders/service.py::refund_order()`. It:
   - rejects orders that aren't settled;
   - inserts the row, and if the key already exists, returns that row instead of calling the provider;
   - calls the gateway and records `succeeded` or `failed`;
   - leaves the row `pending` if the call times out.
4. **UI:** add a Refund button and a status line to the order detail page in `web/order_views.py`. Retrying a failed or pending refund reuses the same key.
5. **Webhook:** update the row by key or `provider_ref`, and ignore rows that are already `succeeded` or `failed`. That makes repeated webhooks harmless.

**The first test to write:** stub the gateway, call `refund_order` twice and deliver the webhook twice. It should show exactly one gateway call and one `succeeded` row. It should also check that a timeout leaves the row `pending` and that a retry doesn't call the provider a second time.

## Risks to settle before step 2
- **Does the provider accept an idempotency key?** Nothing documents it. If it doesn't, a timed-out `pending` refund must be checked with the provider (by order or reference) before any retry. Otherwise retries could refund twice.
- **What should the key be?** For a first version that allows full refunds only, use one key per order. Partial refunds would need a per-request key created when the page loads, and a check that the total refunded never exceeds the amount captured.
- **Callers:** the requirements name `web/order_views.py` as the only caller of `orders/service.py`. In the real repo, search the code to find every caller before landing step 3.

Nothing else broken or unsafe came up, since there was no code to read. The run used about $0.17 and a few minutes, well within budget. Do you want me to go ahead with this, or look at the provider-side idempotency question first?