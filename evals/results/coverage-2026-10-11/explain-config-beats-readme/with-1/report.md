# What happens when a charge fails (`fixture/payments`)

I'm assuming you can read Python but haven't seen this service. Everything below is **traced**: I read all 7 files. I didn't run anything, and the gateway is a stub here (`gateway.py:12-13`).

## What it is
Checkout puts a charge job on a queue (`enqueue.py:7`). A worker takes jobs off and charges the card through the gateway. "A charge fails" can mean two different things here, and the code treats them differently.

## The path

```
checkout -> enqueue.charge_later -> queue -> worker.process -> gateway.charge
                                                  |-- ok         -> "charged"
                                                  |-- Declined   -> "declined"  (stop, nothing recorded)
                                                  `-- Transient  -> sleep, retry
                                                        `-- out of attempts -> dead_letter.put
```

Follow one job through it. Checkout enqueues order 42 with a fresh `idempotency_key` (`enqueue.py:13`). `process` calls `gateway.charge(..., key=...)` (`worker.py:11`). What happens next depends on the exception:

1. **`Declined`** means the card said no. `process` returns `"declined"` immediately (`worker.py:13-14`). It doesn't retry, which is correct, because retrying a decline won't help.
2. **`Transient`** means a timeout, 5xx or rate limit (`gateway.py:8-9`). It sleeps `2 ** attempt` seconds and tries again (`worker.py:18`). With the default of 5 attempts that's sleeps of 2, 4, 8 and 16s, about 30s total. After the last attempt it calls `dead_letter.put(job, reason=...)` and returns `"dead-lettered"` (`worker.py:19-20`).
3. **Dead-lettered jobs** go on a list. The docstring says ops reviews it every morning and retries by hand (`dead_letter.py:1`).

## Why it's built this way
- **The idempotency key is reused on every attempt** (`enqueue.py:12-13`). A `Transient` error means the charge "may or may not have gone through" (`gateway.py:9`). The retry is only safe because the gateway charges at most once per key. Don't change how the key is generated without understanding this.
- **Attempts went from 4 to 5** "after the 2026-06 gateway brownout" (`settings.py:3`). That comment is the only recorded reason. There's no other history here (no git repo, no `WHY.md`).

## What's not obvious
- **The README is wrong.** It says "retried 3 times" (`README.md:4`). The code makes 5 attempts in total, which is 4 retries, and `PAY_MAX_ATTEMPTS` can override that (`settings.py:4`). Trust the code and the env var in the deployed environment, not the README.
- **A decline leaves no trace.** `process` returns `"declined"`, but `run_forever` throws the return value away (`worker.py:25`). Nothing is logged, nothing is stored, and the order isn't told. If a customer says "I was never told my card failed", this is where to look. Whatever tells them has to live outside this folder, and I didn't find it.
- **The queue and dead-letter list are in-memory Python lists** (`queue.py:1`, `dead_letter.py:2`). A worker restart loses every queued job and every dead-lettered job. That includes the list ops reads each morning. I'm assuming production swaps these for something durable. That's **suspected**, because nothing in this folder says so.
- **Nothing in this folder reads or retries the dead-letter list.** `dead_letter.py` only has `put`. The "ops reviews it" step happens outside this code.
- **Other exceptions kill the worker.** `process` only catches `Declined` and `Transient`. Any other error, or `queue.get()` on an empty queue (`IndexError`, `queue.py:9`), propagates out of `run_forever` and stops the loop. The job was already popped, so it's gone.
- **Retries block the worker.** `time.sleep` runs inline (`worker.py:18`). During a gateway outage, each job holds the worker for about 30s before it's dead-lettered.

## Where to look next, by likely page
- **Gateway outage:** check the `settings.py` knobs and whether the dead-letter list is growing.
- **Duplicate-charge report:** check `enqueue.py:13` and the idempotency key's behavior at the gateway.
- **"Customer never knew their card failed":** the `"declined"` return at `worker.py:14`, then find what consumes it downstream.

## Check it landed
Try this one, which I didn't cover. If `gateway.charge` raises `Transient` on attempt 1, then succeeds on attempt 2, what does `process` return, and how many times did the customer's card get charged?

If you want to go further, I can walk through the retry timing or the dead-letter handoff.

Separately: there is no logging anywhere in these files. That matters most on call.