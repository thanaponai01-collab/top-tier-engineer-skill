PRODUCTS = {
    "mug": ("Mug", 1200),
    "tee": ("T-shirt", 2500),
    "cap": ("Cap", 1800),
}


def price_of(sku):
    return PRODUCTS[sku][1]


def name_of(sku):
    return PRODUCTS[sku][0]
