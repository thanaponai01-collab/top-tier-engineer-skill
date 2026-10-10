"""Entry points the web layer calls."""
from billing import credit_notes, invoices


def create(customer, lines):
    return invoices.create(customer, lines)


def send(invoice_id):
    return invoices.send(invoice_id)


def correct(invoice_id, reason):
    return credit_notes.issue(invoice_id, reason)
