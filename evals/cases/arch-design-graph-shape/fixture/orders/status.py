import shipping.tracking
from orders.lines import lines_total


ORDER_STATES = ('placed', 'packed', 'shipped', 'delivered')


def label(order):
    return order['status'].capitalize() + ' (' + shipping.tracking.eta_text(order['id']) + ')'


def advance(order):
    return ORDER_STATES[min(ORDER_STATES.index(order['status']) + 1, len(ORDER_STATES) - 1)]
