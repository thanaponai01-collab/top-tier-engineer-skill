from inventory.stock import ON_HAND, available
from core.util import clamp


def reserve(sku, qty):
    if available(sku) < qty:
        raise ValueError(f'short on {sku}')
    ON_HAND[sku] -= qty


def release(sku, qty):
    ON_HAND[sku] = ON_HAND.get(sku, 0) + qty
