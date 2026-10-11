"""Tools the assistant can call."""
from shop import orders, payments, mail


def lookup_order(order_id):
    return orders.get(order_id)


def issue_refund(order_id, amount):
    return payments.refund(order_id, amount)        # limit enforced in payments


def email_customer(to, body):
    return mail.send(to, body)


TOOLS = {"lookup_order": lookup_order, "issue_refund": issue_refund, "email_customer": email_customer}
