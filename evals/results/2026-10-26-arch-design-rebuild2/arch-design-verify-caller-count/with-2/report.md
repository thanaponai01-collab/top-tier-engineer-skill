Yes, it's safe to remove `ShippingCalculator` (`shipping/base.py:8`), but it isn't unused, and deleting the file alone will break things. One other file has to change first.

**Why it looks unused:** nothing calls it directly. Checkout (`checkout/cart.py:1`) and the nightly reprice job (`jobs/reprice.py:2`, where it's imported under the alias `pick_calc`) only use `get_calculator` from the registry. There are no `isinstance` checks or type hints that mention it.

**Why it isn't:** `FlatRateCalculator` inherits from it, and every caller goes through it on import: `cart.py` → `registry.py:1` → `flat_rate.py:1` → `shipping.base`. I tried this in a temporary copy. With `base.py` deleted and nothing else changed, both checkout and the reprice job fail on import with `ModuleNotFoundError: No module named 'shipping.base'`.

**What has to change (one file, two lines, then the delete):**
1. In `shipping/flat_rate.py`, delete line 1 (`from shipping.base import ShippingCalculator`) and change line 4 to `class FlatRateCalculator:`.
2. Delete `shipping/base.py`.

Nothing else needs editing. `registry.py`, `cart.py`, `reprice.py` and the `"flat"` key don't change.

**Check that passes before and after each step** (run from `fixture/`; I ran it on the original code and on the edited copy, and it printed `ok` both times):
```
python -B -c "from checkout.cart import total_with_shipping; from jobs.reprice import reprice_open_orders; o=[{'subtotal':10}]; reprice_open_orders(o); assert o[0]['shipping']==5.0; assert total_with_shipping({'subtotal':10})==15.0; print('ok')"
```

**Should you remove it?** I'd say yes. Overall the structure is clean. The base class only raises `NotImplementedError`, and the registry (`CALCULATORS` in `shipping/registry.py:3`) already lets you pick a carrier by name. A second carrier would be one new class plus one dict entry. Keeping the base class means two places define what a carrier is.

The option I'm not recommending is keeping it, or turning it into a `typing.Protocol`, for a second carrier that may come later. If that turns out to be wrong, adding a Protocol back is about 10 lines in one file, with no data migration and no change to callers. Since the code hasn't shipped, this is easy to undo.

**Noticed along the way (not about structure):** `get_calculator` raises a bare `KeyError` for an unknown carrier name, and shipping costs are floats (`5.00`), which can cause rounding errors with money.

The audit changed nothing in `fixture/`, and the skill's gate check passed. Do you want me to make the edit, or look into either of the side issues first?