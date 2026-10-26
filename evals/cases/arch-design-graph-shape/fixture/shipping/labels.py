from core.util import slug
from customers.addresses import default_address


def label_text(cid, order_id):
    return f"{order_id} -> {(default_address(cid) or {}).get('city', '?')}"
