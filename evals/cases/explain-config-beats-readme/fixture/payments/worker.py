"""The worker loop: take a job, try to charge it, retry transient failures."""
import time

from . import dead_letter, gateway, queue, settings


def process(job):
    """Try to charge `job`. Returns "charged", "declined" or "dead-lettered"."""
    for attempt in range(1, settings.MAX_ATTEMPTS + 1):
        try:
            gateway.charge(job["card_token"], job["amount_cents"], key=job["idempotency_key"])
            return "charged"
        except gateway.Declined:
            return "declined"                       # the card said no: retrying won't help
        except gateway.Transient:
            if attempt == settings.MAX_ATTEMPTS:
                break
            time.sleep(settings.BACKOFF_BASE_S ** attempt)
    dead_letter.put(job, reason="gave up after transient errors")
    return "dead-lettered"


def run_forever():
    while True:
        process(queue.get())
