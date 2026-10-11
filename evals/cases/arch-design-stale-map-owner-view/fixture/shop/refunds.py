from shop import payments
from shop.jobs.queue import enqueue


def refund(customer, order, amount):
    refund = payments.refund(order["charge_id"], amount)
    enqueue("send_refund_confirmation", {"to": customer["email"], "refund": refund})
    return refund
