**Short answer:** Yes, you can remove it, but not by deleting the file alone. It's only "unused" from the callers' side. Inside `shipping/` it is still the base class of the one calculator that does real work.

## Structure

Five files. Every caller goes through the registry:

```
checkout/cart.py  ──┐
                    ├──> shipping/registry.py ──> shipping/flat_rate.py ──> shipping/base.py
jobs/reprice.py   ──┘    (get_calculator)          (FlatRateCalculator)      (ShippingCalculator)
```

- `shipping/base.py:8` defines `ShippingCalculator`. Its only method is `quote()`, which just raises `NotImplementedError`.
- `shipping/flat_rate.py:4` defines `FlatRateCalculator(ShippingCalculator)`, which returns `5.00`.
- `shipping/registry.py:3` maps `"flat"` to `FlatRateCalculator`, and `get_calculator()` creates an instance.
- `checkout/cart.py` and `jobs/reprice.py` call `get_calculator("flat").quote(order)`. `reprice.py` imports it under the alias `pick_calc`, so searching for `get_calculator(` calls won't find that caller, but it's still a live use of the registry.

## Why it looks unused, and why it isn't

Neither consumer ever mentions `ShippingCalculator`. Nothing in the fixture uses it in a type hint, an `isinstance`/`issubclass` check, `__subclasses__`, or a dynamic import. It adds no behaviour either: `FlatRateCalculator` overrides the only method. So it's dead as an abstraction.

It is not dead as an import, though. If you delete `base.py` on its own, `flat_rate.py:1` raises `ImportError`. That import runs when `registry.py` loads, so both checkout totals and the nightly reprice job would fail at import time. Only two references exist in the fixture, and both are in `flat_rate.py`.

## What has to change

Only `shipping/flat_rate.py`:

```python
class FlatRateCalculator:
    """The only shipping calculator in production."""

    def quote(self, order):
        return 5.00
```

1. Remove `from shipping.base import ShippingCalculator` (line 1).
2. Change `class FlatRateCalculator(ShippingCalculator):` to `class FlatRateCalculator:` (line 4).
3. Delete `shipping/base.py`.

`registry.py`, `cart.py` and `reprice.py` need no changes. They rely only on `get_calculator` and a `.quote()` method, and both stay.

## Caveats

- **Code outside the fixture:** I only searched `fixture/`. Anything else that imports `shipping.base` or subclasses `ShippingCalculator`, like another repo, a plugin or tests, can't be seen here. Search for it before deleting, since that's how "unused everywhere I checked" usually goes wrong.
- **Losing the seam:** The docstring says the class is kept "in case a second carrier is ever needed." Removing it costs little: the registry is the real extension point, and Python duck typing means a second calculator only needs a `quote()` method. If you want to keep a documented contract, a `typing.Protocol` does that without an inheritance import. But YAGNI supports deleting it.
- **No tests:** The fixture has none, so nothing automatically catches the `ImportError`. After the change, running `python -c "import checkout.cart, jobs.reprice"` from inside `fixture/` is a quick check.

I haven't changed any files. Say if you want me to apply the edit.