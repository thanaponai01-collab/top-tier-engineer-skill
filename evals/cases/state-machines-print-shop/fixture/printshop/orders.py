from . import stock
from .guards import allowed_from
from .models import OrderError


def checkout(order):
    if order.status != "draft":
        raise OrderError(f"cannot check out an order that is {order.status}")
    stock.reserve(order.pages)
    order.status = "awaiting_payment"


def pay(order, now):
    if order.status != "awaiting_payment":
        raise OrderError(f"cannot pay for an order that is {order.status}")
    order.status = "paid"
    order.paid_at = now


def cancel(order):
    if order.status not in ("draft", "awaiting_payment", "paid"):
        raise OrderError(f"cannot cancel an order that is {order.status}")
    if order.status != "draft":
        stock.release(order.pages)
    order.status = "cancelled"


def refund(order):
    if order.status != "canceled" or order.paid_at is None:
        raise OrderError("only cancelled orders that were paid can be refunded")
    if order.refunded:
        raise OrderError("already refunded")
    order.refunded = True


def start_print(order, job):
    if order.status != "paid":
        raise OrderError(f"cannot print an order that is {order.status}")
    order.status = "printing"
    if not job.start(order):
        order.status = "paid"
        return False
    return True


def ship(order):
    order.status = "shipped"


@allowed_from("shipped")
def archive(order):
    order.status = "archived"
