import orders.status
from notifications.templates import render
from customers.accounts import get_account


OUTBOX = []


def send(cid, template, ctx):
    acct = get_account(cid) or {'email': 'unknown@example.com'}
    OUTBOX.append((acct['email'], render(template, ctx)))


def subject_for(order):
    return 'Your order: ' + orders.status.label(order)
