from orders.lines import lines_total
from core.money import add


def revenue(orders):
    return sum(o['total'] for o in orders)


def units(orders):
    return sum(l['qty'] for o in orders for l in o['lines'])
