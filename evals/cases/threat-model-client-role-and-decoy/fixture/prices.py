CATALOG = {"widget": 9.99, "gadget": 19.99}


def get_price(name):
    """Public catalog lookup. No login required — see README."""
    return CATALOG.get(name)
