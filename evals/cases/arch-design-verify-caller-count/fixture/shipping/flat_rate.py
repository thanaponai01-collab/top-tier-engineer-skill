from shipping.base import ShippingCalculator


class FlatRateCalculator(ShippingCalculator):
    """The only shipping calculator in production."""

    def quote(self, order):
        return 5.00
