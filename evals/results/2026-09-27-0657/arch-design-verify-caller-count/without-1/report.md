**Short answer:** Yes, you can remove it safely. But it isn't actually unused, so deleting the file by itself would break everything. You have to change one other file along with it.

## Structure

```
checkout/cart.py    ──┐
                      ├─> shipping/registry.py ──> shipping/flat_rate.py ──> shipping/base.py
jobs/reprice.py     ──┘     get_calculator()        FlatRateCalculator        ShippingCalculator
                            (imported as pick_calc)   .quote() -> 5.00          .quote() -> NotImplementedError
```

- `shipping/base.py:8`: `ShippingCalculator` is the interface. It's an abstract-style base class with a single `quote()` that raises `NotImplementedError`.
- `shipping/flat_rate.py:4`: `FlatRateCalculator(ShippingCalculator)` is the only implementation.
- `shipping/registry.py`: a `{"flat": FlatRateCalculator}` dict plus `get_calculator(name)`.
- Both consumers get a calculator through the registry and just call `.quote(order)`. `jobs/reprice.py:2` imports it under the alias `pick_calc`, so searching for call sites of `get_calculator(` won't find that one.

## Why it looks unused, and why it isn't

Neither consumer mentions `ShippingCalculator`. There are no type hints, no `isinstance` or `issubclass` checks, and nothing in the registry refers to it. Callers rely only on the object having a `quote()` method. That's probably why it looked dead.

It does have one real use: `flat_rate.py` imports it and inherits from it. If you delete `shipping/base.py` alone, `from shipping.base import ShippingCalculator` raises `ImportError`. That breaks `registry.py`, which in turn breaks both `checkout/cart.py` and `jobs/reprice.py`.

## What has to change

Two edits and nothing else:

1. Delete `shipping/base.py`.
2. In `shipping/flat_rate.py`, drop the import and the base class:
   ```python
   class FlatRateCalculator:
       """The only shipping calculator in production."""

       def quote(self, order):
           return 5.00
   ```

`registry.py`, `cart.py` and `reprice.py` don't need to change. The base class adds no behaviour: `FlatRateCalculator` overrides `quote()` and there's no shared state or helper code. So nothing changes at runtime.

## Caveats

- **What I checked:** everything in `fixture/`. There are no tests, no `__init__.py` re-exports, and no string references to the class. If code outside this tree subclasses or type-checks against `shipping.base.ShippingCalculator` (plugins, another repo, stubs), it would break. Since this hasn't shipped yet, that's unlikely.
- **The "seam" argument is weak.** The docstring says the class is kept "in case a second carrier is ever needed", but the real extension point is the `CALCULATORS` dict in the registry. A second carrier only needs a class with a `quote()` method and one entry in that dict. If you want to keep a documented contract without a base class, a `typing.Protocol` would do it with no runtime coupling. Otherwise, removing it is fine.