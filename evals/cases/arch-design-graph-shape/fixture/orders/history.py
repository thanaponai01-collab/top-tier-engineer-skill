from core.clock import now
from core.util import chunks


LOG = []


def record(order_id, event):
    LOG.append((now(), order_id, event))


def pages(n):
    return chunks(LOG, n)
