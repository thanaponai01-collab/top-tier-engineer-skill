Here's the failure path, from checkout to giving up.

When checkout wants money it calls charge_later in payments/enqueue.py:7. That puts a job on the
queue with a fresh idempotency key. The key is generated once there and travels with the job.

The worker (payments/worker.py:7, process) then tries to charge. There are two kinds of failure.
A Declined from the gateway is final: the function returns "declined" and nothing retries. A Transient
error, which is a timeout, a 5xx or a rate limit, gets retried with backoff.

How many times? Not what the README says. The loop runs to settings.MAX_ATTEMPTS, which defaults to
5 in payments/settings.py:4 (you can override it with PAY_MAX_ATTEMPTS). Sleeps are 2, 4, 8 and 16
seconds between tries. When the fifth try also fails, the job lands in dead_letter for the morning
ops review.

The part that keeps this safe is the idempotency key. On a timeout you don't know whether the card
was charged. Because every retry sends the same key, the gateway won't charge twice.
