from core.util import clamp


ON_HAND = {}


def receive(sku, qty):
    ON_HAND[sku] = ON_HAND.get(sku, 0) + qty


def available(sku):
    return max(0, ON_HAND.get(sku, 0))
