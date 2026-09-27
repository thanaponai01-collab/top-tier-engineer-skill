"""Shipping cost abstraction.

Kept as a seam in case a second carrier is ever needed. Today only one
implementation exists.
"""


class ShippingCalculator:
    def quote(self, order):
        raise NotImplementedError
