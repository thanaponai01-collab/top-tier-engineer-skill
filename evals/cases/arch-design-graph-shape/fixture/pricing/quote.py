import urllib.request
from catalog.products import base_price
from pricing.discounts import apply_code
from core.money import scale


RATES_URL = "https://rates.example.internal/v1/margin"


def _fetch_margin():
    try:
        with urllib.request.urlopen(RATES_URL, timeout=2) as r:
            return float(r.read())
    except OSError:
        return 1.0


def unit_price(sku, code=None):
    cents = scale(base_price(sku), _fetch_margin())
    return apply_code(cents, code) if code else cents
