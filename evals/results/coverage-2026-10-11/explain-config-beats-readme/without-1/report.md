When a charge fails, there are two paths, depending on the exception `gateway.charge` raises. All the logic is in `fixture/payments/worker.py:7-20`.

**How a job gets there**
1. Checkout calls `charge_later` (`enqueue.py:7`). It puts a job on the queue with a fresh `idempotency_key`.
2. `run_forever` (`worker.py:23`) pulls jobs off the queue and calls `process(job)` on each.

**Path 1: the card is declined (`gateway.Declined`)**
- `process` returns `"declined"` immediately, with no retry (`worker.py:13-14`).
- Nothing is written to the dead-letter list, and nothing is logged or re-queued.
- `run_forever` ignores the return value, so a declined job leaves no trace in this code. If the product needs to tell the customer or mark the order failed, nothing here does that. Check whether it happens somewhere else.

**Path 2: a transient failure (`gateway.Transient`: timeout, 5xx or rate limit)**
- The worker retries up to `MAX_ATTEMPTS` times, counting the first try.
- It sleeps `2 ** attempt` seconds between tries, so 2s, 4s, 8s and 16s. That is about 30s of sleeping in total.
- The sleep blocks the worker, so one failing job stalls everything behind it.
- After the last attempt, the job goes to `dead_letter.put(job, reason="gave up after transient errors")` and `process` returns `"dead-lettered"`.
- The dead-letter module's docstring says ops reviews that list every morning and retries by hand.

**Things to know before you're on call**
- **The README is wrong about retries.** It says 3 retries. `settings.py:4` defaults `PAY_MAX_ATTEMPTS` to 5 (4 retries), which was raised from 4 after the June 2026 gateway brownout. Check the value set in your deployed environment.
- **A transient error doesn't mean the charge failed.** `gateway.py:9` says the charge "may or may not have gone through".
- **The same `idempotency_key` is used on every attempt.** The key is created once in `enqueue.py`, and per its comment the gateway charges at most once per key. That makes both the automatic retries and a manual replay of a dead-lettered job safe from double charges, as long as you replay the original job with its original key. Don't re-enqueue it through `charge_later`, which would mint a new key.
- **The queue and dead-letter list are plain in-memory Python lists** (`queue.py`, `dead_letter.py`). A worker restart loses anything pending or dead-lettered. This may be a stand-in in this copy, so confirm what production uses.
- **In this copy `gateway.charge` always raises `Transient`.** The network code is elided, so every job here ends up dead-lettered.

Two things to ask your team: where declines get surfaced, and how ops actually retries from the dead-letter list. I didn't find either in this directory.