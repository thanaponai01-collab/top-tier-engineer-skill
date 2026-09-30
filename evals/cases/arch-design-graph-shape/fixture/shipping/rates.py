from core.money import scale
from customers.addresses import default_address


def flat_rate(country):
    return 500 if country == 'US' else 1500


def quote_shipping(cid, weight_g):
    return scale(flat_rate((default_address(cid) or {}).get('country', 'US')), 1 + weight_g / 10000)
