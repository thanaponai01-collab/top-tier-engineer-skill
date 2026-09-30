from catalog.products import PRODUCTS
from core.util import clamp, as_cents, slug, first


def find(term):
    t = term.lower()
    return [p for p in PRODUCTS.values() if t in p['title'].lower()]


def cheapest(term):
    return min(find(term), key=lambda p: p['base_cents'], default=None)
