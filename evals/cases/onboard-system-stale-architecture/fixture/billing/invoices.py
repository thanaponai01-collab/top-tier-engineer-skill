import itertools

import store
from billing import notify

_ids = itertools.count(1)


class AlreadySent(Exception):
    pass


def create(customer, lines):
    inv = {"id": next(_ids), "customer": customer, "lines": list(lines), "sent": False}
    store.INVOICES[inv["id"]] = inv
    return inv["id"]


def total(inv):
    return sum(qty * unit for _, qty, unit in inv["lines"])


def edit(invoice_id, lines):
    inv = store.INVOICES[invoice_id]
    if inv["sent"]:
        raise AlreadySent("sent invoices are immutable; issue a credit note")
    inv["lines"] = list(lines)


def send(invoice_id):
    inv = store.INVOICES[invoice_id]
    if inv["sent"]:
        return False
    inv["sent"] = True
    notify.invoice_sent(inv)
    return True
