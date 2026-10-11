I'll assume you know Python and queues, but not this worker.

**What it is:** checkout drops a charge job on a queue, and this worker charges the card, retrying
only the failures that might succeed next time.

**Following one failing charge:**
1. Checkout calls `charge_later` (`payments/enqueue.py:7`), which creates an **idempotency key once**,
   `uuid4()` at `enqueue.py:13`, and stores it in the job.
2. `process` (`payments/worker.py:7`) loops `for attempt in range(1, settings.MAX_ATTEMPTS + 1)`.
   `MAX_ATTEMPTS` is **5** (`payments/settings.py:4`, env `PAY_MAX_ATTEMPTS`), so it makes up to 5
   attempts: the first plus 4 retries. The README's "3 times" is out of date.
3. `gateway.Declined` returns `"declined"` straight away (`worker.py:13`). A decline is never retried.
4. `gateway.Transient` (timeout, 5xx, rate limit) sleeps `2 ** attempt` s: 2, 4, 8, 16. That's about
   30 s in total before the fifth attempt fails.
5. After the last attempt the job goes to `dead_letter.put` (`worker.py:19`). Ops reviews that list
   each morning and retries by hand.

**Why it's built this way:** a Transient error may mean the charge *did* go through. Every attempt
sends the same key (`worker.py:11`), so the gateway charges at most once per key. Without that,
retries could double-charge. The 5 is from a comment: raised from 4 after the June gateway brownout.

**A case not covered above:** if a job is dead-lettered and ops re-enqueues it through `charge_later`,
it gets a **new** key, so a charge that silently succeeded could be charged again. Worth knowing on call.
