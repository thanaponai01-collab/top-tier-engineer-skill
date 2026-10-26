**Yes, it's safe to remove.** The interface is `ShippingCalculator` in `shipping/base.py`. It isn't quite unused, though: one file depends on it, so deleting only `base.py` would break the import chain for both callers.

## Structure

```
checkout/cart.py     ─┐
                      ├─> shipping/registry.py ─> shipping/flat_rate.py ─> shipping/base.py
jobs/reprice.py      ─┘   get_calculator(name)    FlatRateCalculator       ShippingCalculator
```

- `shipping/base.py:8`: `ShippingCalculator` is an abstract-style class with a single `quote()` that raises `NotImplementedError`. Its docstring says it's a seam kept in case a second carrier is ever needed.
- `shipping/flat_rate.py:4`: `FlatRateCalculator(ShippingCalculator)` is the only implementation. It overrides `quote()` to return `5.00`.
- `shipping/registry.py:3`: `CALCULATORS = {"flat": FlatRateCalculator}`, plus `get_calculator(name)`, which creates the calculator.
- Callers: `checkout/cart.py:5` and `jobs/reprice.py:6` both call `get_calculator("flat").quote(order)`. Note that `reprice.py` imports it under the alias `pick_calc`, so a grep for `get_calculator(` won't find that call. That doesn't affect this deletion, but keep it in mind for any registry changes.

## Why it looked unused, and why it isn't

Neither caller mentions `ShippingCalculator`. They only go through the registry, and nothing does `isinstance(..., ShippingCalculator)` or type-annotates with it. But `flat_rate.py:1` imports it and line 4 inherits from it. If you delete `base.py` alone, importing `flat_rate` raises `ModuleNotFoundError`, which breaks `registry`, and with it `cart.py` and `reprice.py`.

## Why removing it is safe

- The base class adds no behaviour. Its only method is overridden, and it has no `__init__`, state, or helpers.
- Python dispatches `quote()` by duck typing, so the callers don't need the base class.
- Nothing checks types against it, and nothing else subclasses it.

## What has to change

1. Delete `shipping/base.py`.
2. In `shipping/flat_rate.py`, remove the import and the base class:
   ```python
   class FlatRateCalculator:
       """The only shipping calculator in production."""

       def quote(self, order):
           return 5.00
   ```

`registry.py`, `cart.py` and `reprice.py` don't need any changes.

## Caveats

- **What you lose is mostly documentation.** The base class only states the `quote(order)` contract. The registry is the real extension point, so adding a second carrier later just means adding another entry to `CALCULATORS`. If you want to keep the documented contract, a `typing.Protocol` would do it without inheritance, but it isn't required.
- **This only covers `fixture/`.** There are no tests here. If any code outside this directory (other services, plugins, pickled objects) imports `shipping.base`, it will break, so search the wider codebase before merging.