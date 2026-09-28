Yes, it's safe to remove, but it isn't actually unused. Deleting `shipping/base.py` by itself would break every shipping code path. One other file has to change along with it.

**Structure (5 files, 39 lines):**

```
checkout/cart.py    ─┐
                     ├─> shipping/registry.py ─> shipping/flat_rate.py ─> shipping/base.py
jobs/reprice.py     ─┘    get_calculator()        FlatRateCalculator        ShippingCalculator
```

- `shipping/base.py:8`: `ShippingCalculator`, the interface. It only declares `quote()`, which raises `NotImplementedError`.
- `shipping/flat_rate.py:4`: `FlatRateCalculator(ShippingCalculator)`, the only implementation. It returns 5.00.
- `shipping/registry.py`: maps the name `"flat"` to `FlatRateCalculator`. `get_calculator(name)` returns a new instance.
- Two callers use the registry, never the interface directly:
  - `checkout/cart.py:1` imports `get_calculator`.
  - `jobs/reprice.py:2` imports it **under an alias**: `get_calculator as pick_calc`. Searching for `get_calculator(` call sites would miss this nightly job.

**Why it looks unused:** nothing calls `ShippingCalculator`, creates an instance of it, uses it in a type hint, or checks it with `isinstance`/`issubclass`. There's no reflection or dynamic import (`importlib`, `getattr`, `__subclasses__`) either. Its only use is as a base class, which is easy to miss.

**What happens if you just delete `base.py`:** `flat_rate.py:1` (`from shipping.base import ShippingCalculator`) fails with an `ImportError`. Since `registry.py` imports `flat_rate`, both `checkout/cart.py` and `jobs/reprice.py` would fail as soon as they're imported. Checkout would break, and so would the nightly reprice job.

**What actually has to change:**
1. Delete `shipping/base.py`.
2. In `shipping/flat_rate.py`, remove line 1 (the import) and change `class FlatRateCalculator(ShippingCalculator):` to `class FlatRateCalculator:`.

Nothing else needs to change. `registry.py`, `cart.py` and `reprice.py` only rely on `FlatRateCalculator` having a `quote(order)` method, and it still has one. The base class adds no behaviour: its `quote()` is always overridden.

**Two things worth knowing:**
- There are no tests in `fixture/`, so no test run will catch a mistake here. Check it by importing both `checkout.cart` and `jobs.reprice` after the change.
- The docstring in `base.py` says it was kept on purpose "as a seam in case a second carrier is ever needed." Removing it is technically safe; whether to do it is a design call. If a second carrier shows up later, the registry already gives you a place to add it, so re-adding the interface would be cheap.

I didn't change any files.