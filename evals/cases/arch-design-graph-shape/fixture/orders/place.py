from orders.lines import build_lines, lines_total
from inventory.reserve import reserve
from pricing.tax import tax_for
from customers.addresses import default_address
from core.ids import new_id
from shipping.rates import quote_shipping


def place_order(cid, items, gateway, code=None):
    lines = build_lines(items, code)
    country = (default_address(cid) or {}).get('country', 'US')
    subtotal = lines_total(lines)
    total = subtotal + tax_for(subtotal, country) + quote_shipping(cid, 500 * len(lines))
    for l in lines:
        reserve(l['sku'], l['qty'])
    return {'id': new_id('ord'), 'customer': cid, 'lines': lines, 'total': total, 'charge': gateway.charge(cid, total), 'status': 'placed'}
