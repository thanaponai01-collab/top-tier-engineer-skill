**Short version:** a failed charge goes one of two ways. A decline is dropped with no record. A transient error is retried up to 5 times, then moved to a dead-letter list that ops reviews by hand. Everything below is *traced*: I read all 7 files, and I didn't run anything.

## What it is for
Checkout calls `charge_later` (`enqueue.py:7`). That puts a job on a queue, and a single worker charges the card through the gateway.

## The failure path

```
queue.get() → process(job) ─ gateway.charge(..., key=idempotency_key)
                 ├─ ok         → "charged"
                 ├─ Declined   → "declined"      (worker.py:13-14, final, nothing recorded)
                 └─ Transient  → sleep 2^attempt, retry (worker.py:15-18)
                                  └─ after attempt 5 → dead_letter.put → "dead-lettered"
```

Take a job whose gateway call times out every time:
- It makes 5 attempts, with sleeps of 2, 4, 8 and 16s between them. That's about 30s in which the worker does nothing else.
- Then `dead_letter.put(job, reason="gave up after transient errors")` runs (`worker.py:19`).
- The whole job goes onto the dead list, including its `idempotency_key`.

## What is not obvious
1. **The README is wrong about retries.** It says "retried 3 times" (`README.md:4`). The code makes 5 attempts, which is 4 retries (`settings.py:4`). The comment says it was raised from 4 after the 2026-06 gateway brownout. You can also change it with the `PAY_MAX_ATTEMPTS` env var, so check what production actually sets.
2. **Declines are silent.** `process` returns `"declined"`, but `run_forever` throws the return value away (`worker.py:25`). There's no log, metric or alert. If decline rates spike, nothing here will tell you.
3. **"Transient" doesn't mean the charge failed.** The gateway docstring says it "may or may not have gone through" (`gateway.py:8`). Double charges are prevented by the idempotency key. It's created once per charge and reused on every attempt (`enqueue.py:12-13`). **Any manual retry must reuse the job's original key.** Never build a fresh job from the order.
4. **The dead-letter list is a Python list in memory** (`dead_letter.py:2`). The docstring says ops reviews it every morning, but a worker restart or deploy empties it. The queue is the same (`queue.py:1`). In this copy, a crash or deploy loses both queued jobs and dead-lettered ones. I'm assuming production uses real storage, since this fixture says "network elided". Confirm that before your on-call week.
5. **The worker can die.** `queue.get()` calls `pop(0)` on an empty list and raises `IndexError` (`queue.py:9`). `process` only catches `Declined` and `Transient`, so any other exception ends `run_forever` (`worker.py:23-25`), and the job it had already popped is gone. I'd expect production to differ, but I can't tell from this code.
6. **Retries block the worker.** Sleeps are inline (`worker.py:18`). During a gateway brownout, each job holds the worker for about 30s, so the queue backs up behind it.

## Where to look next
- **Dead-letter alert fires:** `dead_letter.py`, then find where production stores it. Retry using the stored job so the key is reused.
- **Backlog growing:** `worker.py:18` and `settings.py`.
- **Customer says they were declined or double-charged:** `gateway.py` and the idempotency key in `enqueue.py`.

I couldn't see how the worker is deployed, where the dead-letter list really lives, or who gets alerted. Ask your team those three things.

**Check:** a job gets `Transient` on attempts 1 and 2, then succeeds on attempt 3. What does `process` return, and does the dead-letter list change? What if the third attempt raises `Declined`?

Separately: the README, the queue behavior and the silent decline path are real gaps. I haven't changed anything.