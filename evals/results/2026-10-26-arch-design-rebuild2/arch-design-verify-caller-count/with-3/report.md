**Short answer:** Yes. `ShippingCalculator` in `shipping/base.py` is safe to remove. It looks unused because nothing depends on it as an interface, but it isn't dead: `FlatRateCalculator` inherits from it, so deleting just `base.py` would break the import in `flat_rate.py`. You need to change two files, not one. I checked this by running both money paths in a throwaway copy before and after removing it. The gate came back `ARCH-GATE: done`, and nothing in `fixture/` was changed.

**Verdict:** messy in places. There's an extra layer kept "in case a second carrier is needed" that gives no protection and adds a file to read on every shipping change.

### Finding: a base class with one subclass that nothing relies on
- **Where:** `shipping/base.py:8`, `shipping/flat_rate.py:1`, `shipping/flat_rate.py:4`
- **Evidence:** I ran the checkout and the nightly reprice job before and after deleting it, and both gave the same results.
- **Cost:** one extra file on every shipping change. Nothing uses it for an `isinstance`/`issubclass` check, a type hint or a dynamic lookup, so it enforces nothing. `raise NotImplementedError` only fires when someone calls it. The thing that actually lets you swap carriers is the `CALCULATORS` dict in `shipping/registry.py:3`.

### Move: delete `ShippingCalculator`; the registry stays the way to add carriers
1. In `shipping/flat_rate.py`, remove line 1 (`from shipping.base import ShippingCalculator`) and change line 4 to `class FlatRateCalculator:`.
2. Delete `shipping/base.py`.

**Callers:** only `shipping/flat_rate.py:1` and `:4` reference the interface.

**Be careful here:** these other files use the shipping code and must not be "cleaned up" along with it. A plain search for the class or function name will miss two of them:
- `checkout/cart.py:5` gets the calculator with `get_calculator("flat")`, a lookup by string.
- `jobs/reprice.py:2,6` imports it under a different name (`get_calculator as pick_calc`) and also looks it up by `"flat"`. This is the nightly repricing job.
- `shipping/registry.py:1,3` holds `CALCULATORS = {"flat": FlatRateCalculator}`.

So `FlatRateCalculator` and the registry are in active use even if a search makes them look unused. Only the base class can go.

**Proof** (run from `fixture/`; it passes today and after each step):
```
python -B -c "from checkout.cart import total_with_shipping as t; from jobs.reprice import reprice_open_orders as r; o=[{'subtotal':10}]; r(o); assert t({'subtotal':10})==15.0 and o[0]['shipping']==5.0; print('ok')"
```

- **Door:** two-way, meaning it's easy to undo. It touches no stored data, public API or auth.
- **Reuses:** `shipping/registry.py:3`, which already handles picking a carrier by name. A second carrier would be one new class and one dict entry.
- **Not adding:** a second place that claims to define "a calculator" next to the registry, when nothing checks it.
- **Rejected option:** keep the base and make it a real contract (`typing.Protocol` or an `abc.ABC` with an abstract `quote`).
- **Cost if this is wrong:** if a second carrier shows up, adding a Protocol back is about 5 lines in one file. Keeping the base means a permanent extra layer that suggests a guarantee it doesn't give.

### Found in passing (not structure)
- `quote` returns `5.00` as a float and the totals add floats. Money held as floats will pick up rounding errors once real rates or taxes come in. Integer cents or `Decimal` would avoid that.
- `get_calculator` raises a bare `KeyError` for an unknown carrier name, so a typo in the nightly job would crash the whole batch without a clear message.

Do you want to go ahead with this move, or would you rather keep the seam and make it a real `Protocol`?