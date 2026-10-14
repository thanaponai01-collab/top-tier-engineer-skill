# SPEC.md: done

Pricing is in `shop/cart.py`; the five new modules (shipping, inventory, orders, gift cards,
loyalty) are under `shop/`, and the invoice has its new lines.

`python acceptance/check.py` prints `ACCEPTANCE: 21/21 passed` and `python -m unittest` is green.
The acceptance check was left as is.
