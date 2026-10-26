import time

from shop import emailer
from shop.jobs.queue import next_job

HANDLERS = {
    "send_refund_confirmation": lambda p: emailer.send_refund_confirmation(p["to"], p["refund"]),
}


def run_forever():
    while True:
        job = next_job()
        if job is None:
            time.sleep(1)
            continue
        task, payload = job
        HANDLERS[task](payload)
