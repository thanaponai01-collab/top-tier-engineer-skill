from pricing.quote import unit_price
from core.util import clamp


def build_lines(items, code=None):
    return [{'sku': i['sku'], 'qty': clamp(i['qty'], 1, 99), 'cents': unit_price(i['sku'], code)} for i in items]


def lines_total(lines):
    return sum(l['cents'] * l['qty'] for l in lines)
