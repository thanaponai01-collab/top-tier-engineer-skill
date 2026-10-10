"""Customer emails (was billing/mailer.py until 2026-09-02)."""
import store


def invoice_sent(inv):
    store.OUTBOX.append(("invoice", inv["customer"], inv["id"]))


def credit_note_issued(note):
    store.OUTBOX.append(("credit_note", note["customer"], note["id"]))
