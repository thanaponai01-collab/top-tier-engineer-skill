from core.util import clamp, as_cents, slug, first


PRODUCTS = {}


def add_product(sku, title, base_cents):
    PRODUCTS[sku] = {'sku': sku, 'title': title, 'base_cents': base_cents, 'slug': slug(title)}
    return PRODUCTS[sku]


def get_product(sku):
    return PRODUCTS.get(sku)


def base_price(sku):
    return PRODUCTS[sku]['base_cents']
