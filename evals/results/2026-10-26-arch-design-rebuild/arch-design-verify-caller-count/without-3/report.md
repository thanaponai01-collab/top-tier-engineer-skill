**Yes, it's safe to remove, but it isn't unused.** One file has to change along with the deletion.

**Structure (5 files, 39 lines):**

```
shipping/base.py       ShippingCalculator: abstract quote() that raises NotImplementedError
shipping/flat_rate.py  FlatRateCalculator(ShippingCalculator): quote() returns 5.00
shipping/registry.py   CALCULATORS = {"flat": FlatRateCalculator}; get_calculator(name)
checkout/cart.py       get_calculator("flat").quote(order)
jobs/reprice.py        same call, imported under the alias `pick_calc`
```

**Where it's used**

`ShippingCalculator` in `shipping/base.py` has no callers. Nothing creates it, type-hints it, or checks `isinstance` against it. Both consumers (`cart.py` and `reprice.py`) only use the registry and call `.quote()`. That's probably why it looked unused.

But it has one real reference: `shipping/flat_rate.py` imports it and uses it as the base class.

- If you delete `base.py` alone, `flat_rate.py` breaks on import.
- That takes down `registry.py`, which in turn breaks both checkout and the nightly reprice job.

So "unused everywhere I checked" probably means they looked for callers and missed the subclass.

**Why removing it changes nothing at runtime**

The base class contributes no behaviour. `FlatRateCalculator` overrides its only method, and no code relies on the type. Callers just call `.quote()` on whatever the registry returns.

**What has to change**

1. Delete `shipping/base.py`.
2. In `shipping/flat_rate.py`, remove the `from shipping.base import ShippingCalculator` import and change the class line to `class FlatRateCalculator:`.

`registry.py`, `cart.py` and `reprice.py` don't need any changes.

**Before deleting**

- **Look outside `fixture/`.** I could only see these five files, and there are no tests here. Search the wider codebase for `ShippingCalculator` and `shipping.base` (tests, plugins, type stubs). The text search also needs to catch aliased imports like the `as pick_calc` one in `reprice.py`.
- **It's a design choice, not just cleanup.** The docstring in `base.py` says it was kept on purpose, as a placeholder in case a second carrier is ever needed. Dropping it is reasonable while there's only one implementation; it's easy to add back if a second one arrives. If they want to keep the documented contract without the inheritance, they could replace it with a `typing.Protocol`, but at this size that isn't needed.

I haven't changed any files.