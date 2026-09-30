from inventory.stock import available


SITES = {'east': ['A', 'B'], 'west': ['C']}


def site_for(sku):
    return 'east' if available(sku) else 'west'
