"""A shopping cart: quantities per sku."""
from shop import catalog


class Cart:
    def __init__(self):
        self.lines = {}

    def add(self, sku, qty=1):
        if qty < 1:
            raise ValueError("qty must be at least 1")
        catalog.price(sku)  # rejects unknown skus
        self.lines[sku] = self.lines.get(sku, 0) + qty

    def line_total(self, sku):
        return catalog.price(sku) * self.lines[sku]

    def subtotal(self):
        return sum(self.line_total(sku) for sku in self.lines)
