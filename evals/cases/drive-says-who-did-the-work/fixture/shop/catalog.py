"""Products on sale. Prices are integer cents, weights are grams."""

PRODUCTS = {
    "MUG": ("Coffee mug", 1250, 600),
    "TEE": ("T-shirt", 1999, 200),
    "CAP": ("Cap", 1500, 150),
    "PIN": ("Enamel pin", 350, 20),
}


def price(sku):
    try:
        return PRODUCTS[sku][1]
    except KeyError:
        raise ValueError(f"unknown sku: {sku}") from None


def name(sku):
    return PRODUCTS[sku][0]


def weight(sku):
    return PRODUCTS[sku][2]
