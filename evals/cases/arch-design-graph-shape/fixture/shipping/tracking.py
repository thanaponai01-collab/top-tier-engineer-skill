import notifications.email
from core.clock import now, days


TRACK = {}


def mark_delivered(order_id, cid):
    TRACK[order_id] = now()
    notifications.email.send(cid, 'delivered', {'order': order_id})


def eta_text(order_id):
    return 'delivered' if order_id in TRACK else 'in ~3 days'
