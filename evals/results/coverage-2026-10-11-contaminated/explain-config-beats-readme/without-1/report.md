A failed charge has two outcomes. A decline ends there. Transient errors are retried up to 5 times, and then the job goes to a dead-letter list that a person has to review. *Traced:* I read every file in `fixture/` (about 80 lines) but didn't run any of it.

One thing to know first: the README is out of date. It says "retried 3 times." `settings.py:4` sets `MAX_ATTEMPTS` to 5 by default, and `PAY_MAX_ATTEMPTS` overrides it. Check the env value in production before you trust either number.

## The flow

1. **Enqueue** (`enqueue.py`): checkout calls `charge_later`. It puts a job on the queue with `order_id`, `amount_cents` and `card_token`. It also adds an `idempotency_key`, a fresh uuid made once per charge. Every retry reuses that key, so the gateway charges at most once per key.
2. **Worker loop** (`worker.py:23`): `run_forever` pops a job and calls `process(job)`.
3. **Charge** (`worker.py:11`): `process` calls `gateway.charge(...)`. It can end in one of three ways:

| Gateway result | What the worker does | Returns |
|---|---|---|
| Success | Stops | `"charged"` |
| `Declined` (card said no) | Doesn't retry | `"declined"` |
| `Transient` (timeout, 5xx, rate limit) | Sleeps `2**attempt` seconds and retries. On the last attempt it gives up. | `"dead-lettered"` |

With the defaults the sleeps are 2s, 4s, 8s and 16s, about 30s per job. There is no sleep after the last attempt.

4. **Dead letter** (`dead_letter.py`): the job is stored with the reason "gave up after transient errors". The file's docstring says ops reviews this list every morning and retries by hand.

## What to watch while on call

- **A dead-lettered charge may have gone through.** `Transient` means the charge "may or may not have gone through." Before anyone retries a dead-lettered job by hand, check the gateway for that job's `idempotency_key`. Retrying with the same key is safe. Creating a new job with a new key could double-charge.
- **A decline is only returned, not recorded.** `process` returns `"declined"`, but `run_forever` ignores the return value. Nothing stores the decline, alerts on it, or tells checkout. I found no other code in `fixture/` that handles it. If declines are meant to reach the customer, that happens outside this directory or doesn't happen.
- **A single worker blocks while it sleeps.** `time.sleep` holds the loop, so during a gateway brownout each failing job holds that worker for about 30s. The queue backs up behind it.
- **The queue and dead-letter list are plain in-memory lists** (`queue.py`, `dead_letter.py`). Nothing is persisted, so a restart loses pending and dead-lettered jobs. These look like stand-ins in this copy, as the gateway does (`gateway.py:13` always raises `Transient`). Find out what the real implementations are before your shift.
- **Other exceptions crash the loop.** Only `Declined` and `Transient` are caught. Anything else raised by `gateway.charge` escapes `process` and stops `run_forever`.

## Questions for your team

- What are the production values of `PAY_MAX_ATTEMPTS` and the real queue and dead-letter backends?
- Where does the morning dead-letter review happen, and is it a runbook or a dashboard?
- Is anything supposed to act on declines?

I can write these up as a short on-call runbook if you want one.