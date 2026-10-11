import itertools

import store
from billing import invoices, notify

_ids = itertools.count(1)


def issue(invoice_id, reason):
    inv = store.INVOICES[invoice_id]
    if not inv["sent"]:
        raise ValueError("unsent invoices are edited, not credited")
    note = {"id": next(_ids), "invoice_id": invoice_id, "customer": inv["customer"],
            "amount": -invoices.total(inv), "reason": reason}
    store.CREDIT_NOTES[note["id"]] = note
    notify.credit_note_issued(note)
    return note["id"]
