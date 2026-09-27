"""Nightly job that recomputes shipping on open orders."""
from shipping.registry import get_calculator as pick_calc


def reprice_open_orders(orders):
    calc = pick_calc("flat")
    for order in orders:
        order["shipping"] = calc.quote(order)
