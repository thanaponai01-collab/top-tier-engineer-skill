# How failed charges work

When a charge fails, the worker retries it 3 times with exponential backoff, as described in the README.
If all three retries fail, the charge is given up on.

The retry logic lives in `payments/worker.py`. Declines and network errors are handled in the same
loop, so a declined card will also be retried until the attempts run out.

That's the whole flow. The main thing to watch on call is gateway errors.
